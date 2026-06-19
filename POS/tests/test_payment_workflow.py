"""
Tests for Payment Workflow.

Covers:
- Payment creation (online + POS / COD)
- Cash register auto-update on COD payments
- Customer ledger auto-update on payment
- Payment verification (initiated -> captured)
- Payment status transitions (with validation)
- Payment refund (full + partial)
- Refund restock_items option
- Invalid transition prevention
- Duplicate refund prevention
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models import (
    Payment, PaymentEventLog, RefundTransaction,
    Order, OrderItem, Product, Category, Unit,
    CashRegister, CashMovement, CustomerLedger,
    POSTerminal, POSShift, InventoryBatch,
)
from POS.services import PaymentService, ShiftService

User = get_user_model()


class PaymentWorkflowTest(TestCase):
    """Test payment lifecycle: create -> verify -> capture -> refund."""

    @classmethod
    def setUpTestData(cls):
        cls.employee = User.objects.create_user(
            name='Employee', email='emp@pay.test', password='testpass123',
        )
        cls.employee.role = 'salesman'
        cls.employee.is_active = True
        cls.employee.save()

        cls.customer = User.objects.create_user(
            name='Customer', email='cust@pay.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        cls.category = Category.objects.create(name='Pay Cat', slug='pay-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='Pay Product', slug='pay-prod', sku='PAY-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("100.00"), selling_price=Decimal("100.00"),
            created_by=cls.employee,
        )

        cls.terminal = POSTerminal.objects.create(
            name='Pay Terminal', terminal_code='PAY-T-001',
            location='Counter 1', is_active=True,
            created_by=cls.employee,
        )

    def setUp(self):
        """Create a fresh order and shift for each test."""
        self.order = Order.objects.create(
            order_number=f'ORD-PAY-{timezone.now().timestamp():.0f}',
            user=self.customer,
            subtotal=Decimal("500.00"),
            total_amount=Decimal("500.00"),
            status='pending',
            payment_status='unpaid',
            created_by=self.employee,
        )
        OrderItem.objects.create(
            order=self.order, product=self.product,
            quantity=5, unit_price=Decimal("100.00"),
            total_price=Decimal("500.00"), cost_price=Decimal("50.00"),
        )
        # Fresh stock
        InventoryBatch.objects.create(
            product=self.product, cost_price=Decimal("50.00"),
            received_quantity=100, remaining_quantity=100,
            purchase_date='2026-01-01', is_active=True,
        )
        Product.objects.filter(id=self.product.id).update(base_stock=100)

    def _create_cash_register(self):
        """Helper: create shift + register for COD tests."""
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.employee,
            status='open',
            created_by=self.employee,
        )
        register = CashRegister.objects.create(
            terminal=self.terminal, shift=shift,
            opening_balance=Decimal("1000.00"),
            expected_closing_balance=Decimal("1000.00"),
            status='open', opened_by=self.employee,
            opened_at=timezone.now(),
        )
        return shift, register

    # =========================================================================
    #  PAYMENT CREATION
    # =========================================================================

    def test_create_cash_payment_updates_register(self):
        """COD payment must update CashRegister expected balance."""
        shift, register = self._create_cash_register()

        payment = PaymentService.create_payment(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"),
            payment_method='cash',
            is_cod=True,
            cash_register=register,
            created_by=self.employee,
        )

        self.assertEqual(payment.status, 'captured')
        self.assertEqual(payment.payment_channel, 'cod')
        self.assertTrue(payment.is_cod)

        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("1500.00"))

    def test_create_card_payment_does_not_update_register(self):
        """Non-COD payment must NOT affect CashRegister."""
        shift, register = self._create_cash_register()

        payment = PaymentService.create_payment(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"),
            payment_method='card',
            is_cod=False,
            created_by=self.employee,
        )

        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("1000.00"))
        self.assertFalse(payment.is_cod)

    def test_cod_payment_requires_cash_register(self):
        """COD without register must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            PaymentService.create_payment(
                order=self.order, user=self.customer,
                amount=Decimal("500.00"),
                payment_method='cash',
                is_cod=True,
                cash_register=None,
                created_by=self.employee,
            )
        self.assertIn('Cash register is required', str(ctx.exception))

    def test_create_payment_creates_customer_ledger(self):
        """Payment must create a customer ledger entry."""
        payment = PaymentService.create_payment(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"),
            payment_method='mobile_banking',
            is_cod=False,
            created_by=self.employee,
        )

        ledger = CustomerLedger.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger.transaction_type, 'payment')
        self.assertEqual(ledger.amount, Decimal("500.00"))

    # =========================================================================
    #  PAYMENT VERIFICATION
    # =========================================================================

    def test_verify_payment_changes_status(self):
        """Verify transitions INITIATED -> CAPTURED."""
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='initiated',
            payment_method='card',
        )

        verified = PaymentService.verify_payment(payment)
        self.assertEqual(verified.status, 'captured')
        self.assertIsNotNone(verified.paid_at)

        # Verify event log created
        log = PaymentEventLog.objects.filter(payment=payment).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, 'payment_verified')

    def test_verify_captured_payment_raises_error(self):
        """Cannot verify a payment already in CAPTURED status."""
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='captured',
            payment_method='card',
        )
        with self.assertRaises(ValueError):
            PaymentService.verify_payment(payment)

    # =========================================================================
    #  PAYMENT STATUS TRANSITIONS
    # =========================================================================

    def test_valid_status_transition(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='initiated',
            payment_method='card',
        )
        updated = PaymentService.update_payment_status(payment, 'processing')
        self.assertEqual(updated.status, 'processing')

    def test_invalid_status_transition_raises_error(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='initiated',
            payment_method='card',
        )
        with self.assertRaises(ValueError) as ctx:
            PaymentService.update_payment_status(payment, 'refunded')
        self.assertIn('Cannot transition', str(ctx.exception))

    def test_status_transition_creates_event_log(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='initiated',
            payment_method='card',
        )
        PaymentService.update_payment_status(payment, 'processing')
        log = PaymentEventLog.objects.filter(payment=payment).first()
        self.assertEqual(log.event_type, 'status_change_initiated_to_processing')

    # =========================================================================
    #  REFUND
    # =========================================================================

    def test_full_refund_marks_payment_refunded(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='captured',
            payment_method='cash', is_cod=True,
        )
        refund = PaymentService.refund_payment(
            payment=payment, amount=Decimal("500.00"),
            refund_reason='Customer request',
            created_by=self.employee,
        )
        self.assertEqual(refund.amount, Decimal("500.00"))
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'refunded')

    def test_partial_refund_keeps_payment_captured(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='captured',
            payment_method='card',
        )
        refund = PaymentService.refund_payment(
            payment=payment, amount=Decimal("200.00"),
            refund_reason='Partial return',
            created_by=self.employee,
        )
        self.assertEqual(refund.amount, Decimal("200.00"))
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'captured')

    def test_refund_exceeds_remaining_balance_raises_error(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='captured',
            payment_method='card',
        )
        # First refund 300
        PaymentService.refund_payment(
            payment=payment, amount=Decimal("300.00"),
            refund_reason='Partial', created_by=self.employee,
        )
        # Second refund 300 exceeds remaining 200
        with self.assertRaises(ValueError) as ctx:
            PaymentService.refund_payment(
                payment=payment, amount=Decimal("300.00"),
                refund_reason='Over refund', created_by=self.employee,
            )
        self.assertIn('exceeds remaining balance', str(ctx.exception))

    def test_refund_non_captured_payment_raises_error(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='initiated',
            payment_method='card',
        )
        with self.assertRaises(ValueError):
            PaymentService.refund_payment(
                payment=payment, amount=Decimal("500.00"),
                refund_reason='Test', created_by=self.employee,
            )

    def test_refund_with_restock_adds_inventory(self):
        """Verify restock_items=True adds items back to inventory.
        Uses InventoryBatch sum for accurate stock tracking since
        batch cache may be synced during the operation."""
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='captured',
            payment_method='cash', is_cod=True,
        )

        # Count batches before refund
        from POS.models import InventoryBatch
        batch_count_before = InventoryBatch.objects.filter(
            product=self.product, is_active=True,
        ).count()

        PaymentService.refund_payment(
            payment=payment, amount=Decimal("500.00"),
            refund_reason='Full refund + restock',
            created_by=self.employee,
            restock_items=True,
        )

        # New batch should have been created
        batch_count_after = InventoryBatch.objects.filter(
            product=self.product, is_active=True,
        ).count()
        self.assertEqual(batch_count_after, batch_count_before + 1)

    def test_refund_creates_event_log(self):
        payment = Payment.objects.create(
            order=self.order, user=self.customer,
            amount=Decimal("500.00"), status='captured',
            payment_method='card',
        )
        PaymentService.refund_payment(
            payment=payment, amount=Decimal("200.00"),
            refund_reason='Test', created_by=self.employee,
        )
        log = PaymentEventLog.objects.filter(payment=payment).first()
        self.assertEqual(log.event_type, 'refund_processed')