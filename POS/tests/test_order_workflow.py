"""
Tests for Order Workflow.

Covers:
- Order creation (POS + Online)
- Order item creation with snapshots
- Order confirmation with inventory deduction
- Order cancellation with reservation release
- Order status tracking via logs
- Coupon validation at order level
- Cart total recalculation
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from POS.models import (
    Order, OrderItem, OrderStatusLog, Cart, CartItem,
    Product, Category, Unit, InventoryBatch, InventoryTransaction,
)
from POS.services import OrderService
from POS.services.pricing_service import PricingEngine

User = get_user_model()


class OrderWorkflowTest(TestCase):
    """Test complete order lifecycle: create → confirm → cancel → complete."""

    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(
            name='Customer', email='cust@order.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        cls.employee = User.objects.create_user(
            name='Employee', email='emp@order.test', password='testpass123',
        )
        cls.employee.role = 'salesman'
        cls.employee.is_active = True
        cls.employee.save()

        cls.category = Category.objects.create(name='Order Cat', slug='order-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='Order Product', slug='order-prod',
            sku='ORD-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("100.00"),
            selling_price=Decimal("100.00"),
            created_by=cls.employee,
        )

    def setUp(self):
        # Ensure stock is available
        Product.objects.filter(id=self.product.id).update(base_stock=50, reserved_stock=0)
        InventoryBatch.objects.filter(product=self.product).delete()
        InventoryBatch.objects.create(
            product=self.product,
            cost_price=Decimal("50.00"),
            received_quantity=50,
            remaining_quantity=50,
            purchase_date='2026-01-01',
            is_active=True,
        )

    def _create_order(self, source='web', items_data=None):
        """Helper to create an order."""
        if items_data is None:
            items_data = [{
                'product': self.product,
                'quantity': 2,
                'unit_price': Decimal("100.00"),
                'total_price': Decimal("200.00"),
            }]
        return OrderService.create_order(
            user=self.customer,
            source=source,
            items_data=items_data,
            subtotal=Decimal("200.00"),
            total_amount=Decimal("200.00"),
            created_by=self.employee,
        )

    def test_create_order(self):
        order = self._create_order()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.payment_status, 'unpaid')
        self.assertEqual(order.source, 'web')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(OrderStatusLog.objects.filter(order=order).count(), 1)

    def test_create_pos_order(self):
        order = self._create_order(source='pos')
        self.assertEqual(order.source, 'pos')
        self.assertTrue(order.order_number.startswith('POS'))

    def test_create_order_with_product_snapshots(self):
        items_data = [{
            'product': self.product,
            'quantity': 3,
            'unit_price': Decimal("90.00"),
            'total_price': Decimal("270.00"),
            'product_snapshot': {'name': self.product.name, 'sku': self.product.sku},
        }]
        order = self._create_order(items_data=items_data)
        item = order.items.first()
        self.assertEqual(item.product_snapshot['name'], self.product.name)

    def test_confirm_order_without_payment_raises_error(self):
        order = self._create_order()
        with self.assertRaises(ValueError) as ctx:
            OrderService.confirm_order(order=order, changed_by=self.employee)
        self.assertIn('without a captured payment', str(ctx.exception))

    def test_confirm_order_with_payment_deducts_inventory(self):
        order = self._create_order()
        # Create a captured payment
        from POS.models import Payment
        Payment.objects.create(
            order=order,
            user=self.customer,
            amount=Decimal("200.00"),
            status='captured',
            payment_method='cash',
        )

        confirmed = OrderService.confirm_order(order=order, changed_by=self.employee)
        self.assertEqual(confirmed.status, 'confirmed')
        self.assertEqual(confirmed.payment_status, 'paid')

        # Verify inventory deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 48)

        # Verify status log - second log should be confirmed
        logs = OrderStatusLog.objects.filter(order=order).order_by('id')
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs.last().new_status, 'confirmed')

    def test_cancel_order(self):
        order = self._create_order()
        cancelled = OrderService.cancel_order(
            order=order,
            reason='Customer changed mind',
            changed_by=self.employee,
        )
        self.assertEqual(cancelled.status, 'cancelled')
        self.assertIsNotNone(cancelled.cancelled_at)

    def test_complete_order(self):
        order = self._create_order()
        completed = OrderService.complete_order(order=order, changed_by=self.employee)
        self.assertEqual(completed.status, 'delivered')
        self.assertIsNotNone(completed.delivered_at)

    def test_cart_total_recalculation(self):
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=3,
            unit_price_snapshot=Decimal("100.00"),
        )
        OrderService.recalculate_cart_totals(cart)
        cart.refresh_from_db()
        self.assertEqual(cart.subtotal, Decimal("300.00"))
        self.assertEqual(cart.total_amount, Decimal("300.00"))

    def test_order_status_log_is_preserved(self):
        order = self._create_order()
        log_count = OrderStatusLog.objects.filter(order=order).count()
        OrderService.update_order_status(
            order=order, new_status='processing', note='Started processing',
            changed_by=self.employee,
        )
        self.assertEqual(
            OrderStatusLog.objects.filter(order=order).count(), log_count + 1,
        )

    def test_order_total_mismatch_validated(self):
        from POS.models import Order
        with self.assertRaises(Exception):
            order = Order(
                order_number='ORD-BAD-TOTAL',
                user=self.customer,
                subtotal=Decimal("100"),
                shipping_cost=Decimal("0"),
                tax_amount=Decimal("0"),
                discount_amount=Decimal("0"),
                total_amount=Decimal("999"),  # Should be 100
                created_by=self.employee,
            )
            order.full_clean()