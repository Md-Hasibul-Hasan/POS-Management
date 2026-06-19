"""
Tests for Exchange Workflow.

Covers:
- Exchange request creation with old/new variants
- Exchange approval
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from POS.models import (
    ExchangeRequest, Order, OrderItem,
    Product, Category, Unit, Payment, ProductVariant,
)

User = get_user_model()


class ExchangeWorkflowTest(TestCase):
    """Test exchange workflow: request -> approve."""

    @classmethod
    def setUpTestData(cls):
        cls.employee = User.objects.create_user(
            name='Employee', email='emp@exc.test', password='testpass123',
        )
        cls.employee.role = 'salesman'
        cls.employee.is_active = True
        cls.employee.save()

        cls.customer = User.objects.create_user(
            name='Customer', email='cust@exc.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        cls.category = Category.objects.create(name='Exc Cat', slug='exc-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.old_product = Product.objects.create(
            name='Old Product', slug='old-prod', sku='OLD-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
            created_by=cls.employee,
        )
        cls.new_product = Product.objects.create(
            name='New Product', slug='new-prod', sku='NEW-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("150.00"), selling_price=Decimal("150.00"),
            created_by=cls.employee,
        )

        # Create variants since ExchangeRequest requires old_variant and new_variant
        cls.old_variant = ProductVariant.objects.create(
            product=cls.old_product, name='Old Variant',
            slug='old-var-exc', sku='OLD-VAR-EXC-001',
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
        )
        cls.new_variant = ProductVariant.objects.create(
            product=cls.new_product, name='New Variant',
            slug='new-var-exc-new', sku='NEW-VAR-EXC-001',
            base_price=Decimal("150.00"), selling_price=Decimal("150.00"),
        )

        cls.order = Order.objects.create(
            order_number='ORD-EXC-001', user=cls.customer,
            subtotal=Decimal("100.00"), total_amount=Decimal("100.00"),
            status='delivered', payment_status='paid',
            created_by=cls.employee,
        )
        cls.order_item = OrderItem.objects.create(
            order=cls.order, product=cls.old_product,
            quantity=1, unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"), cost_price=Decimal("50.00"),
        )
        Payment.objects.create(
            order=cls.order, user=cls.customer,
            amount=Decimal("100.00"), status='captured',
            payment_method='cash',
        )

    def test_create_exchange_request(self):
        exchange = ExchangeRequest.objects.create(
            order=self.order, user=self.customer,
            old_order_item=self.order_item,
            old_variant=self.old_variant,
            new_variant=self.new_variant,
            quantity=1, reason='Wrong size',
            status='pending',
        )
        self.assertEqual(exchange.status, 'pending')
        self.assertEqual(exchange.quantity, 1)
        self.assertEqual(exchange.reason, 'Wrong size')

    def test_approve_exchange(self):
        exchange = ExchangeRequest.objects.create(
            order=self.order, user=self.customer,
            old_order_item=self.order_item,
            old_variant=self.old_variant,
            new_variant=self.new_variant,
            quantity=1, reason='Wrong size',
            status='pending',
        )
        exchange.status = 'approved'
        exchange.save()
        exchange.refresh_from_db()
        self.assertEqual(exchange.status, 'approved')