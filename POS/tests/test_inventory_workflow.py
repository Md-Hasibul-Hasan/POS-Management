"""
Tests for Inventory Workflow.

Covers:
- FIFO batch consumption on stock deduction
- Stock addition from purchases/returns
- Stock reservation and release
- Stock adjustment
- Stock audit
- Damage/lost reporting
- Stock availability checks
- Cache synchronization
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from POS.models import (
    Product, Category, Unit, InventoryBatch, InventoryTransaction,
    StockReservation, StockAdjustment, StockAudit, DamageReport,
)
from POS.services import InventoryService

User = get_user_model()


class InventoryWorkflowTest(TestCase):
    """Test complete inventory lifecycle: add → reserve → deduct → adjust → audit."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            name='Admin', email='admin@inv.test', password='testpass123',
        )
        cls.admin.role = 'admin'
        cls.admin.is_active = True
        cls.admin.save()

        cls.category = Category.objects.create(name='Inventory Cat', slug='inv-cat')
        cls.unit = Unit.objects.create(name='Unit', short_name='u', unit_type='unit')

        cls.product = Product.objects.create(
            name='Inventory Product',
            slug='inv-prod',
            sku='INV-PROD-001',
            category=cls.category,
            unit=cls.unit,
            base_price=Decimal("50.00"),
            created_by=cls.admin,
        )

    def setUp(self):
        Product.objects.filter(id=self.product.id).update(base_stock=0)
        InventoryBatch.objects.all().delete()
        InventoryTransaction.objects.all().delete()

    def _add_stock(self, qty, cost_price=Decimal("10.00"), batch_number=""):
        return InventoryService.add_stock(
            product=self.product,
            quantity=qty,
            cost_price=cost_price,
            performed_by=self.admin,
            batch_number=batch_number,
        )

    # ─────────────────────────────────────────────────────────────────
    #  STOCK ADDITION
    # ─────────────────────────────────────────────────────────────────

    def test_add_stock_creates_batch_and_transaction(self):
        tx = self._add_stock(100)
        self.assertEqual(tx.transaction_type, 'purchase')
        self.assertEqual(tx.quantity, 100)

        batch = InventoryBatch.objects.filter(product=self.product).first()
        self.assertIsNotNone(batch)
        self.assertEqual(batch.remaining_quantity, 100)

        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 100)

    def test_add_stock_zero_quantity_raises_error(self):
        with self.assertRaises(ValueError):
            InventoryService.add_stock(
                product=self.product, quantity=0, cost_price=Decimal("10"),
            )

    # ─────────────────────────────────────────────────────────────────
    #  FIFO STOCK DEDUCTION
    # ─────────────────────────────────────────────────────────────────

    def test_fifo_deduction_consumes_oldest_batch_first(self):
        self._add_stock(10, Decimal("10.00"), "BATCH-001")
        self._add_stock(10, Decimal("20.00"), "BATCH-002")
        self._add_stock(10, Decimal("30.00"), "BATCH-003")

        txs = InventoryService.deduct_stock(
            product=self.product, quantity=25, performed_by=self.admin,
        )
        self.assertEqual(len(txs), 3)

        batches = InventoryBatch.objects.filter(
            product=self.product, is_active=True,
        ).order_by('purchase_date', 'id')

        batch_list = list(batches)
        self.assertEqual(len(batch_list), 1)
        self.assertEqual(batch_list[0].remaining_quantity, 5)
        self.assertEqual(batch_list[0].batch_number, "BATCH-003")

    def test_deduct_insufficient_stock_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            InventoryService.deduct_stock(
                product=self.product, quantity=10, performed_by=self.admin,
            )
        self.assertIn('Insufficient stock', str(ctx.exception))

    def test_deduct_exact_quantity(self):
        self._add_stock(50)
        txs = InventoryService.deduct_stock(
            product=self.product, quantity=50, performed_by=self.admin,
        )
        self.assertEqual(len(txs), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 0)

    # ─────────────────────────────────────────────────────────────────
    #  STOCK RESERVATION
    # ─────────────────────────────────────────────────────────────────

    def test_reserve_stock(self):
        self._add_stock(30)
        from POS.models import Order
        order = Order.objects.create(
            order_number='ORD-RES-001',
            user=self.admin,
            total_amount=Decimal("100"),
        )
        reservation = InventoryService.reserve_stock(
            product=self.product, quantity=5, order=order,
            user=self.admin, performed_by=self.admin,
        )
        self.assertEqual(reservation.quantity, 5)
        self.assertEqual(reservation.status, 'active')
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_stock, 5)

    def test_reserve_insufficient_stock_raises_error(self):
        from POS.models import Order
        order = Order.objects.create(
            order_number='ORD-RES-002', user=self.admin,
            total_amount=Decimal("100"),
        )
        with self.assertRaises(ValueError):
            InventoryService.reserve_stock(
                product=self.product, quantity=100, order=order, user=self.admin,
            )

    def test_release_reservation_restores_available_stock(self):
        self._add_stock(30)
        from POS.models import Order
        order = Order.objects.create(
            order_number='ORD-RES-003', user=self.admin,
            total_amount=Decimal("100"),
        )
        reservation = InventoryService.reserve_stock(
            product=self.product, quantity=10, order=order,
            user=self.admin, performed_by=self.admin,
        )
        released = InventoryService.release_stock(
            reservation=reservation, performed_by=self.admin,
        )
        self.assertEqual(released.status, 'released')
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_stock, 0)

    # ─────────────────────────────────────────────────────────────────
    #  STOCK ADJUSTMENT
    # ─────────────────────────────────────────────────────────────────

    def test_adjust_stock_creates_transaction(self):
        self._add_stock(20)
        old_count = InventoryTransaction.objects.count()
        tx = InventoryService.adjust_stock(
            product=self.product, quantity=5, reason='Manual add',
            performed_by=self.admin,
        )
        # Should create an InventoryTransaction
        self.assertEqual(InventoryTransaction.objects.count(), old_count + 1)
        # Product cache should be updated via _sync_stock_cache
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 25)

    def test_adjust_stock_negative(self):
        self._add_stock(20)
        old_count = InventoryTransaction.objects.count()
        tx = InventoryService.adjust_stock(
            product=self.product, quantity=-5, reason='Manual remove',
            performed_by=self.admin,
        )
        self.assertEqual(InventoryTransaction.objects.count(), old_count + 1)
        self.assertTrue(tx.quantity < 0)

    def test_adjust_stock_below_zero_raises_error(self):
        self._add_stock(5)
        with self.assertRaises(ValueError):
            InventoryService.adjust_stock(
                product=self.product, quantity=-10, reason='Over-deduct',
                performed_by=self.admin,
            )

    # ─────────────────────────────────────────────────────────────────
    #  STOCK AUDIT
    # ─────────────────────────────────────────────────────────────────

    def test_stock_audit_no_variance(self):
        self._add_stock(50)
        audit = InventoryService.perform_audit(
            product=self.product, physical_stock=50, audited_by=self.admin,
        )
        self.assertEqual(audit.variance, 0)
        self.assertEqual(audit.status, 'completed')

    def test_stock_audit_positive_variance_auto_adjusts(self):
        self._add_stock(50)
        old_tx_count = InventoryTransaction.objects.count()
        audit = InventoryService.perform_audit(
            product=self.product, physical_stock=55, audited_by=self.admin,
        )
        self.assertEqual(audit.variance, 5)
        # Should create an adjustment transaction
        self.assertEqual(InventoryTransaction.objects.count(), old_tx_count + 1)

    def test_stock_audit_negative_variance_auto_adjusts(self):
        self._add_stock(50)
        old_tx_count = InventoryTransaction.objects.count()
        audit = InventoryService.perform_audit(
            product=self.product, physical_stock=45, audited_by=self.admin,
        )
        self.assertEqual(audit.variance, -5)
        self.assertEqual(InventoryTransaction.objects.count(), old_tx_count + 1)

    # ─────────────────────────────────────────────────────────────────
    #  DAMAGE REPORTING
    # ─────────────────────────────────────────────────────────────────

    def test_report_damage_deducts_stock(self):
        self._add_stock(30)
        tx = InventoryService.report_damage(
            product=self.product, quantity=3, reason='Broken during handling',
            reported_by=self.admin,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 27)
        damage_reports = DamageReport.objects.filter(product=self.product)
        self.assertEqual(damage_reports.count(), 1)

    # ─────────────────────────────────────────────────────────────────
    #  AVAILABLE STOCK
    # ─────────────────────────────────────────────────────────────────

    def test_get_available_stock(self):
        self._add_stock(20)
        available = InventoryService.get_available_stock(self.product)
        self.assertEqual(available, 20)

    def test_get_available_stock_with_reservation(self):
        self._add_stock(20)
        from POS.models import Order
        order = Order.objects.create(
            order_number='ORD-AVAIL-001', user=self.admin,
            total_amount=Decimal("100"),
        )
        InventoryService.reserve_stock(
            product=self.product, quantity=5, order=order, user=self.admin,
        )
        available = InventoryService.get_available_stock(self.product)
        self.assertEqual(available, 15)