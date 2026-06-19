"""
Tests for Accounting Workflow.

Covers:
- AccountCategory creation (income + expense)
- AccountTransaction creation
- Record sale entries (with tax + shipping)
- Record expense entries
- Record refund entries
- Record inventory adjustment entries
- Idempotency check (skip duplicate sale recording)
- Daily sales report generation
- POS sales report generation
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models import (
    AccountCategory, AccountTransaction, Order, OrderItem,
    Product, Category, Unit,
)
from POS.services import AccountingService

User = get_user_model()


class AccountingWorkflowTest(TestCase):
    """Test complete accounting lifecycle: categorize -> transact -> report."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            name='Admin', email='admin@acct.test', password='testpass123',
        )
        cls.admin.role = 'admin'
        cls.admin.is_active = True
        cls.admin.save()

        cls.category = Category.objects.create(name='Acct Cat', slug='acct-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='Acct Product', slug='acct-prod', sku='ACCT-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
            created_by=cls.admin,
        )

    def _create_order(self):
        """Helper: create a completed order."""
        return Order.objects.create(
            order_number=f'ORD-ACCT-{timezone.now().timestamp():.0f}',
            user=self.admin,
            subtotal=Decimal("1000.00"),
            shipping_cost=Decimal("50.00"),
            tax_amount=Decimal("100.00"),
            discount_amount=Decimal("0"),
            total_amount=Decimal("1150.00"),
            currency='BDT',
            source='web',
            status='confirmed',
            payment_status='paid',
            created_by=self.admin,
        )

    # =========================================================================
    #  ACCOUNT CATEGORY
    # =========================================================================

    def test_create_income_category(self):
        cat = AccountCategory.objects.create(
            name='Test Income', category_type='income',
            is_system=False, created_by=self.admin,
        )
        self.assertEqual(cat.category_type, 'income')
        self.assertIn('Test Income', str(cat))
        self.assertIn('income', str(cat))

    def test_create_expense_category(self):
        cat = AccountCategory.objects.create(
            name='Test Expense', category_type='expense',
            is_system=False, created_by=self.admin,
        )
        self.assertEqual(cat.category_type, 'expense')

    # =========================================================================
    #  ACCOUNT TRANSACTION
    # =========================================================================

    def test_create_transaction_requires_positive_amount(self):
        cat = AccountCategory.objects.create(
            name='Test', category_type='income',
        )
        with self.assertRaises(ValueError):
            AccountingService.create_transaction(
                category=cat, amount=Decimal("0"),
            )

    def test_create_transaction(self):
        cat = AccountCategory.objects.create(
            name='Sales', category_type='income',
            is_system=True,
        )
        tx = AccountingService.create_transaction(
            category=cat, amount=Decimal("500.00"),
            description='Test transaction',
            reference_type='order', reference_id=1,
            created_by=self.admin,
        )
        self.assertEqual(tx.amount, Decimal("500.00"))
        self.assertEqual(tx.reference_type, 'order')
        self.assertEqual(tx.reference_id, 1)

    # =========================================================================
    #  RECORD SALE
    # =========================================================================

    def test_record_sale_creates_entries(self):
        order = self._create_order()
        txs = AccountingService.record_sale(order=order, created_by=self.admin)
        # Should create 3 entries: subtotal + tax + shipping
        self.assertEqual(len(txs), 3)

        for tx in txs:
            self.assertEqual(tx.reference_type, 'order')
            self.assertEqual(tx.reference_id, order.id)

    def test_record_sale_idempotent(self):
        order = self._create_order()
        # First call creates entries
        first_txs = AccountingService.record_sale(order=order, created_by=self.admin)
        self.assertEqual(len(first_txs), 3)

        # Second call should return empty (idempotent)
        second_txs = AccountingService.record_sale(order=order, created_by=self.admin)
        self.assertEqual(len(second_txs), 0)

    def test_record_sale_without_tax_or_shipping(self):
        order = Order.objects.create(
            order_number=f'ORD-SIMPLE-{timezone.now().timestamp():.0f}',
            user=self.admin,
            subtotal=Decimal("500.00"),
            shipping_cost=Decimal("0"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("500.00"),
            created_by=self.admin,
        )
        txs = AccountingService.record_sale(order=order, created_by=self.admin)
        # Should create only 1 entry: subtotal
        self.assertEqual(len(txs), 1)

    # =========================================================================
    #  RECORD EXPENSE
    # =========================================================================

    def test_record_expense(self):
        tx = AccountingService.record_expense(
            amount=Decimal("200.00"),
            description='Office supplies',
            category_name='Office Expense',
            created_by=self.admin,
        )
        self.assertEqual(tx.amount, Decimal("200.00"))
        self.assertEqual(tx.category.name, 'Office Expense')

    def test_record_expense_auto_creates_category(self):
        tx = AccountingService.record_expense(
            amount=Decimal("100.00"),
            description='Utilities',
            category_name='Utility Bills',
            created_by=self.admin,
        )
        cat = AccountCategory.objects.filter(name='Utility Bills').first()
        self.assertIsNotNone(cat)
        self.assertEqual(cat.category_type, 'expense')

    # =========================================================================
    #  RECORD REFUND
    # =========================================================================

    def test_record_refund(self):
        order = self._create_order()
        tx = AccountingService.record_refund(
            order=order, refund_amount=Decimal("200.00"),
            refund_reason='Customer return',
            created_by=self.admin,
        )
        self.assertEqual(tx.amount, Decimal("200.00"))
        self.assertIn('Refund', tx.description)

    # =========================================================================
    #  RECORD INVENTORY ADJUSTMENT
    # =========================================================================

    def test_record_inventory_adjustment(self):
        tx = AccountingService.record_inventory_adjustment(
            amount=Decimal("150.00"),
            description='Damaged goods write-off',
            reference_type='damage_report',
            reference_id=1,
            created_by=self.admin,
        )
        self.assertEqual(tx.amount, Decimal("150.00"))
        self.assertEqual(tx.reference_type, 'damage_report')

    # =========================================================================
    #  DAILY SALES REPORT
    # =========================================================================

    def test_daily_sales_report(self):
        # Create orders for today
        for i in range(3):
            Order.objects.create(
                order_number=f'ORD-REPORT-{i}-{timezone.now().timestamp():.0f}',
                user=self.admin,
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("10.00"),
                shipping_cost=Decimal("5.00"),
                total_amount=Decimal("115.00"),
                status='delivered',
                payment_status='paid',
                created_at=timezone.now(),
                created_by=self.admin,
            )

        report = AccountingService.get_daily_sales_report()
        self.assertEqual(report['order_count'], 3)
        self.assertEqual(report['total_sales'], Decimal("345.00"))
        self.assertEqual(report['total_tax'], Decimal("30.00"))
        self.assertEqual(report['total_shipping'], Decimal("15.00"))

    def test_daily_sales_report_empty_day(self):
        report = AccountingService.get_daily_sales_report(
            date=timezone.now().date() - timezone.timedelta(days=365),
        )
        self.assertEqual(report['order_count'], 0)
        self.assertEqual(report['total_sales'], Decimal("0"))

    # =========================================================================
    #  POS SALES REPORT
    # =========================================================================

    def test_pos_sales_report(self):
        Order.objects.create(
            order_number=f'ORD-POS-RPT-{timezone.now().timestamp():.0f}',
            user=self.admin,
            subtotal=Decimal("200.00"),
            total_amount=Decimal("200.00"),
            source='pos',
            status='confirmed',
            payment_status='paid',
            created_at=timezone.now(),
            created_by=self.admin,
        )
        report = AccountingService.get_pos_sales_report()
        self.assertEqual(report['total_sales'], Decimal("200.00"))
        self.assertEqual(report['order_count'], 1)

    def test_pos_sales_report_excludes_online(self):
        Order.objects.create(
            order_number=f'ORD-ONLINE-{timezone.now().timestamp():.0f}',
            user=self.admin,
            subtotal=Decimal("999.00"),
            total_amount=Decimal("999.00"),
            source='online',
            status='confirmed',
            payment_status='paid',
            created_at=timezone.now(),
            created_by=self.admin,
        )
        report = AccountingService.get_pos_sales_report()
        self.assertEqual(report['total_sales'], Decimal("0"))