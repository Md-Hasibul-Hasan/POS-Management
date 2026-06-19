"""
Tests for POS Workflow — End-to-end POS sale orchestration.

Covers:
- POS shift start/end lifecycle
- Cash register open/close/reconcile
- Complete POS sale (create order → payment → inventory → accounting)
- Walk-in customer creation
- Hold/resume sale
- Cash payment auto-updates register
- Cash movement recording
- Invoice generation
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models import (
    POSTerminal, POSShift, CashRegister, CashMovement,
    Order, OrderItem, Payment, Product, Category, Unit,
    InventoryBatch, InventoryTransaction,
)
from POS.services import POSService, ShiftService, RegisterService

User = get_user_model()


class POSWorkflowTest(TestCase):
    """Test complete POS workflow: shift → sale → close → reconcile."""

    @classmethod
    def setUpTestData(cls):
        cls.cashier = User.objects.create_user(
            name='Cashier', email='cashier@pos.test', password='testpass123',
        )
        cls.cashier.role = 'salesman'
        cls.cashier.is_active = True
        cls.cashier.save()

        cls.customer = User.objects.create_user(
            name='Customer', email='cust@pos.test', password='testpass123',
        )
        cls.customer.role = 'customer'
        cls.customer.is_active = True
        cls.customer.save()

        cls.category = Category.objects.create(name='POS Cat', slug='pos-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='POS Product', slug='pos-prod', sku='POS-PROD-001',
            category=cls.category, unit=cls.unit,
            base_price=Decimal("50.00"), selling_price=Decimal("50.00"),
            created_by=cls.cashier,
        )

        cls.terminal = POSTerminal.objects.create(
            name='Main Terminal', terminal_code='T-001',
            location='Front Counter', is_active=True,
            created_by=cls.cashier,
        )

    def setUp(self):
        # Ensure stock
        Product.objects.filter(id=self.product.id).update(base_stock=100)
        InventoryBatch.objects.filter(product=self.product).delete()
        InventoryBatch.objects.create(
            product=self.product, cost_price=Decimal("25.00"),
            received_quantity=100, remaining_quantity=100,
            purchase_date='2026-01-01', is_active=True,
        )

    def test_start_shift_creates_register(self):
        result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("1000.00"),
        )
        shift = result['shift']
        register = result['register']

        self.assertEqual(shift.status, 'open')
        self.assertEqual(shift.cashier, self.cashier)
        self.assertEqual(register.opening_balance, Decimal("1000.00"))
        self.assertEqual(register.status, 'open')

    def test_overlapping_shift_raises_error(self):
        ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("500.00"),
        )
        with self.assertRaises(ValueError):
            ShiftService.start_shift(
                terminal=self.terminal, cashier=self.cashier,
            )

    def test_complete_pos_sale(self):
        # Start shift
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("1000.00"),
        )
        shift = shift_result['shift']

        # Complete sale
        sale_result = POSService.create_pos_sale(
            terminal=self.terminal,
            shift=shift,
            cashier=self.cashier,
            customer=self.customer,
            items=[{
                'product': self.product,
                'quantity': 2,
                'unit_price': Decimal("50.00"),
            }],
            payments=[{
                'payment_method': 'cash',
                'amount': Decimal("100.00"),
                'is_cod': True,
            }],
        )

        order = sale_result['order']
        payments = sale_result['payments']

        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].amount, Decimal("100.00"))

        # Verify inventory deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 98)

        # Verify register balance updated
        register = shift.cash_register
        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("1100.00"))

    def test_pos_sale_with_multiple_payments(self):
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("500.00"),
        )
        shift = shift_result['shift']

        sale_result = POSService.create_pos_sale(
            terminal=self.terminal,
            shift=shift,
            cashier=self.cashier,
            customer=self.customer,
            items=[{
                'product': self.product,
                'quantity': 3,
                'unit_price': Decimal("50.00"),
            }],
            payments=[
                {'payment_method': 'cash', 'amount': Decimal("100.00"), 'is_cod': True},
                {'payment_method': 'card', 'amount': Decimal("50.00"), 'is_cod': False},
            ],
        )

        self.assertEqual(len(sale_result['payments']), 2)
        register = shift.cash_register
        register.refresh_from_db()
        # Only cash payment affects register
        self.assertEqual(register.expected_closing_balance, Decimal("600.00"))

    def test_hold_and_resume_sale(self):
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("500.00"),
        )
        shift = shift_result['shift']

        # Hold sale
        held_order = POSService.hold_sale(
            terminal=self.terminal, shift=shift,
            cashier=self.cashier, customer=self.customer,
            items=[{'product': self.product, 'quantity': 2, 'unit_price': Decimal("50.00")}],
        )
        self.assertEqual(held_order.status, 'pending')

        # Resume sale with payment
        resume_result = POSService.resume_sale(
            held_order=held_order,
            payments=[{'payment_method': 'cash', 'amount': Decimal("100.00"), 'is_cod': True}],
            cashier=self.cashier,
        )
        self.assertEqual(resume_result['order'].status, 'confirmed')

    def test_end_shift_calculates_totals(self):
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("1000.00"),
        )
        shift = shift_result['shift']

        POSService.create_pos_sale(
            terminal=self.terminal, shift=shift,
            cashier=self.cashier, customer=self.customer,
            items=[{'product': self.product, 'quantity': 1, 'unit_price': Decimal("50.00")}],
            payments=[{'payment_method': 'cash', 'amount': Decimal("50.00"), 'is_cod': True}],
        )

        # End shift
        end_result = ShiftService.end_shift(
            shift=shift,
            actual_closing_balance=Decimal("1050.00"),
            closed_by=self.cashier,
        )

        self.assertEqual(end_result['shift'].status, 'closed')
        self.assertEqual(end_result['register'].status, 'closed')
        self.assertIsNotNone(end_result['discrepancy'])

    def test_cash_movement_tracking(self):
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("1000.00"),
        )
        shift = shift_result['shift']
        register = shift_result['register']

        # Record cash out (expense)
        movement = RegisterService.record_cash_movement(
            register=register, shift=shift,
            movement_type='expense', amount=Decimal("50.00"),
            note='Office supplies', created_by=self.cashier,
        )
        self.assertEqual(movement.movement_type, 'expense')

        register.refresh_from_db()
        self.assertEqual(register.expected_closing_balance, Decimal("950.00"))

    def test_create_walkin_customer(self):
        walkin = POSService.create_walkin_customer(
            cashier=self.cashier, phone='+8801700000000', name='Walk-in',
        )
        self.assertIsNotNone(walkin)
        self.assertTrue(walkin.email.endswith('@walkin.local'))

    def test_generate_invoice(self):
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("1000.00"),
        )
        shift = shift_result['shift']

        sale_result = POSService.create_pos_sale(
            terminal=self.terminal, shift=shift,
            cashier=self.cashier, customer=self.customer,
            items=[{'product': self.product, 'quantity': 2, 'unit_price': Decimal("50.00")}],
            payments=[{'payment_method': 'cash', 'amount': Decimal("100.00"), 'is_cod': True}],
        )
        invoice = POSService.generate_invoice(sale_result['order'])
        self.assertIn('invoice_number', invoice)
        self.assertIn('items', invoice)
        self.assertEqual(len(invoice['items']), 1)

    def test_disputed_register_cannot_process_sales(self):
        shift_result = ShiftService.start_shift(
            terminal=self.terminal, cashier=self.cashier,
            opening_balance=Decimal("1000.00"),
        )
        shift = shift_result['shift']
        register = shift_result['register']

        RegisterService.mark_disputed(register)

        with self.assertRaises(ValueError):
            POSService.create_pos_sale(
                terminal=self.terminal, shift=shift,
                cashier=self.cashier, customer=self.customer,
                items=[{'product': self.product, 'quantity': 1, 'unit_price': Decimal("50.00")}],
                payments=[{'payment_method': 'cash', 'amount': Decimal("50.00"), 'is_cod': True}],
            )