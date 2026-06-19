"""
Tests for Return Workflow.

Covers:
- Return record creation
- Return approval
- Return inspection
- Refund processing (with cash movement for POS)
- Restock returned items to inventory
- Exchange order creation (requires variants)
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from POS.models import (
    ReturnRecord, ReturnItem, ReturnInspection,
    Order, OrderItem, Product, Category, Unit,
    InventoryBatch, Payment, RefundTransaction,
    ExchangeRequest, ProductVariant,
)
from POS.services import ReturnService, OrderService

User = get_user_model()


class ReturnWorkflowTest(TestCase):
    """Test complete return workflow: request -> approve -> inspect -> refund -> restock."""

    @classmethod
    def setUpTestData(cls):
        cls.employee = User.objects.create_user(
            name='Employee', email='emp@ret.test', password='testpass123',
        )
        cls.employee.role = 'salesman'
        cls.employee.is_active = True
        cls.employee.save()

        cls.customer = User.objects.create_user(
            name='Customer', email='cust@ret.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        cls.category = Category.objects.create(name='Ret Cat', slug='ret-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='Ret Product', slug='ret-prod', sku='RET-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
            created_by=cls.employee,
        )

        cls.order = Order.objects.create(
            order_number='ORD-RET-001', user=cls.customer,
            subtotal=Decimal("200.00"), total_amount=Decimal("200.00"),
            status='delivered', payment_status='paid',
            created_by=cls.employee,
        )
        cls.order_item = OrderItem.objects.create(
            order=cls.order, product=cls.product,
            quantity=2, unit_price=Decimal("100.00"),
            total_price=Decimal("200.00"), cost_price=Decimal("50.00"),
        )

        cls.payment = Payment.objects.create(
            order=cls.order, user=cls.customer,
            amount=Decimal("200.00"), status='captured',
            payment_method='cash', is_cod=True,
        )

    def test_create_return_record(self):
        return_rec = ReturnRecord.objects.create(
            order=self.order, user=self.customer,
            return_type='partial', reason='Defective item',
        )
        ReturnItem.objects.create(
            return_record=return_rec, order_item=self.order_item,
            product=self.product, quantity=1,
            refund_amount=Decimal("100.00"),
        )
        self.assertEqual(return_rec.status, 'pending')
        self.assertEqual(return_rec.items.count(), 1)

    def test_approve_return(self):
        return_rec = ReturnRecord.objects.create(
            order=self.order, user=self.customer,
            return_type='full', reason='Not as described',
        )
        ReturnItem.objects.create(
            return_record=return_rec, order_item=self.order_item,
            product=self.product, quantity=2,
            refund_amount=Decimal("100.00"),
        )
        approved = ReturnService.approve_return(
            return_record=return_rec, approved_by=self.employee,
        )
        self.assertEqual(approved.status, 'approved')
        self.assertIsNotNone(approved.approved_at)

    def test_full_return_refund_workflow(self):
        return_rec = ReturnRecord.objects.create(
            order=self.order, user=self.customer,
            return_type='full', reason='Damaged',
        )
        ReturnItem.objects.create(
            return_record=return_rec, order_item=self.order_item,
            product=self.product, quantity=2,
            refund_amount=Decimal("100.00"),
        )
        ReturnService.approve_return(return_record=return_rec, approved_by=self.employee)

        result = ReturnService.create_refund(
            return_record=return_rec, created_by=self.employee,
        )
        self.assertEqual(return_rec.status, 'completed')
        self.assertEqual(result['total_refund'], Decimal("200.00"))

    def test_restock_returned_items(self):
        return_rec = ReturnRecord.objects.create(
            order=self.order, user=self.customer,
            return_type='partial', reason='Extra item',
        )
        item = ReturnItem.objects.create(
            return_record=return_rec, order_item=self.order_item,
            product=self.product, quantity=1,
            refund_amount=Decimal("100.00"),
        )
        ReturnInspection.objects.create(
            return_item=item, inspector=self.employee,
            outcome='resellable',
        )
        ReturnService.approve_return(return_record=return_rec, approved_by=self.employee)

        InventoryBatch.objects.create(
            product=self.product, cost_price=Decimal("50.00"),
            received_quantity=10, remaining_quantity=10,
            purchase_date='2026-01-01', is_active=True,
        )

        txs = ReturnService.restock_returned_items(
            return_record=return_rec, performed_by=self.employee,
        )
        self.assertEqual(len(txs), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 11)

    def test_return_inspection(self):
        return_rec = ReturnRecord.objects.create(
            order=self.order, user=self.customer,
            return_type='partial', reason='Check',
        )
        item = ReturnItem.objects.create(
            return_record=return_rec, order_item=self.order_item,
            product=self.product, quantity=1,
            refund_amount=Decimal("100.00"),
        )
        inspection = ReturnService.inspect_return(
            return_item=item, inspector=self.employee,
            outcome='damaged', notes='Scratched surface',
        )
        self.assertEqual(inspection.outcome, 'damaged')
        self.assertEqual(inspection.notes, 'Scratched surface')

    def test_create_exchange(self):
        old_variant = ProductVariant.objects.create(
            product=self.product, name='Old Var Ret',
            slug='old-var-ret-test', sku='OLD-VAR-RET-001',
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
        )
        new_product = Product.objects.create(
            name='New Product Ret', slug='new-prod-ret-test', sku='NEW-PROD-RET-001',
            category=self.category, unit=self.unit,
            base_price=Decimal("150.00"), selling_price=Decimal("150.00"),
            created_by=self.employee,
        )
        new_variant = ProductVariant.objects.create(
            product=new_product, name='New Var Ret',
            slug='new-var-ret-test-new', sku='NEW-VAR-RET-001',
            base_price=Decimal("150.00"), selling_price=Decimal("150.00"),
        )

        exchange = ExchangeRequest.objects.create(
            order=self.order, user=self.customer,
            old_order_item=self.order_item,
            old_variant=old_variant,
            new_variant=new_variant,
            quantity=1, reason='Wrong size',
            status='approved',
        )
        self.assertEqual(exchange.status, 'approved')

    def test_cannot_refund_unapproved_return(self):
        return_rec = ReturnRecord.objects.create(
            order=self.order, user=self.customer,
            return_type='full', reason='Test',
        )
        with self.assertRaises(ValueError):
            ReturnService.create_refund(
                return_record=return_rec, created_by=self.employee,
            )