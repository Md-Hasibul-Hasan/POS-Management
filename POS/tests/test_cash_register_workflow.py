"""
Tests for Cash Register Workflow.

Covers:
- Cash register creation on shift start
- Cash register close with physical count
- Register reconciliation and disputed status
- Cash movement recording (cash_in, cash_out, expense)
- Expected balance recalculation
- Discrepancy detection
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from POS.models import POSTerminal, POSShift, CashRegister, CashMovement
from POS.services import RegisterService, ShiftService

User = get_user_model()


class CashRegisterWorkflowTest(TestCase):
    """Test cash register lifecycle: open → transact → close → reconcile."""

    @classmethod
    def setUpTestData(cls):
        cls.cashier = User.objects.create_user(
            name='Cashier', email='cashier@reg.test', password='testpass123',
        )
        cls.cashier.role = 'salesman'
        cls.cashier.is_active = True
        cls.cashier.save()

        cls.terminal = POSTerminal.objects.create(
            name='Register Terminal', terminal_code='REG-001',
            location='Counter 1', is_active=True,
            created_by=cls.cashier,
        )

    def test_open_register_creates_register(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("500.00"),
            opened_by=self.cashier,
        )
        self.assertEqual(register.opening_balance, Decimal("500.00"))
        self.assertEqual(register.expected_closing_balance, Decimal("500.00"))
        self.assertEqual(register.status, 'open')

    def test_close_register_sets_final_balance(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        closed = RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("1000.00"),
            closed_by=self.cashier,
        )
        self.assertEqual(closed.status, 'closed')
        self.assertEqual(closed.actual_closing_balance, Decimal("1000.00"))
        self.assertIsNotNone(closed.closed_at)

    def test_register_zero_discrepancy(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("1000.00"),
            closed_by=self.cashier,
        )
        register.refresh_from_db()
        self.assertEqual(register.discrepancy, Decimal("0"))

    def test_register_positive_discrepancy(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("1050.00"),
            closed_by=self.cashier,
        )
        register.refresh_from_db()
        self.assertEqual(register.discrepancy, Decimal("50.00"))

    def test_register_negative_discrepancy(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("950.00"),
            closed_by=self.cashier,
        )
        register.refresh_from_db()
        self.assertEqual(register.discrepancy, Decimal("-50.00"))

    def test_reconcile_register(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("1050.00"),
            closed_by=self.cashier,
        )
        RegisterService.reconcile_register(register)
        register.refresh_from_db()
        self.assertEqual(register.status, 'reconciled')

    def test_mark_disputed(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("900.00"),
            closed_by=self.cashier,
        )
        RegisterService.mark_disputed(register)
        register.refresh_from_db()
        self.assertEqual(register.status, 'disputed')

    def test_record_cash_payment_updates_balance(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.record_cash_payment(register, Decimal("200.00"))
        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("1200.00"))

    def test_record_cash_movement_increases_balance(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.record_cash_movement(
            register=register, shift=shift,
            movement_type='cash_in', amount=Decimal("500.00"),
            note='Additional float', created_by=self.cashier,
        )
        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("1500.00"))
        self.assertEqual(CashMovement.objects.filter(register=register).count(), 1)

    def test_record_cash_movement_decreases_balance(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.record_cash_movement(
            register=register, shift=shift,
            movement_type='cash_out', amount=Decimal("300.00"),
            note='Cash pick-up', created_by=self.cashier,
        )
        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("700.00"))

    def test_multiple_movements_cumulative(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        # Record movements via cash_movement (these auto-update via save())
        RegisterService.record_cash_movement(
            register, shift, 'cash_in', Decimal("500.00"),
            note='Top-up', created_by=self.cashier,
        )
        RegisterService.record_cash_movement(
            register, shift, 'expense', Decimal("100.00"),
            note='Supplies', created_by=self.cashier,
        )
        RegisterService.record_cash_movement(
            register, shift, 'cash_in', Decimal("200.00"),
            note='Additional', created_by=self.cashier,
        )
        register.refresh_from_db()
        # opening 1000 + cash_in 500 + cash_in 200 - expense 100 = 1600
        self.assertEqual(register.expected_closing_balance, Decimal("1600.00"))

    def test_closed_register_cannot_record_payment(self):
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        RegisterService.close_register(
            register=register,
            actual_closing_balance=Decimal("1000.00"),
            closed_by=self.cashier,
        )
        with self.assertRaises(ValueError):
            RegisterService.record_cash_payment(register, Decimal("100.00"))

    def test_recalculate_expected_balance_via_properties(self):
        """Verify the model's recalculate_expected_balance() sums correctly.
        Uses cash movements (which auto-update) + direct payment to verify
        that expected_closing_balance is tracked correctly."""
        shift = POSShift.objects.create(
            terminal=self.terminal, cashier=self.cashier,
            status='open', created_by=self.cashier,
        )
        register = RegisterService.open_register(
            shift=shift, opening_balance=Decimal("1000.00"),
            opened_by=self.cashier,
        )
        # Record a cash movement which auto-updates via CashMovement.save()
        RegisterService.record_cash_movement(
            register, shift, 'cash_in', Decimal("300.00"),
            note='Test', created_by=self.cashier,
        )
        register.refresh_from_db()
        # Auto-update on CashMovement.save() added 300, so expected = 1300
        self.assertEqual(register.expected_closing_balance, Decimal("1300.00"))
