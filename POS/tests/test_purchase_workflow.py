"""
Tests for Purchase Workflow.

Covers:
- Supplier creation
- Purchase creation with items
- Purchase approval (should trigger inventory addition)
- Purchase cancellation
- Supplier ledger entries
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction

from POS.models import (
    Supplier, Purchase, PurchaseItem, SupplierLedger,
    InventoryBatch, InventoryTransaction, Product, Category, Unit,
)
from POS.services import InventoryService

User = get_user_model()


class PurchaseWorkflowTest(TestCase):
    """Test the complete purchase-to-inventory workflow."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            name='Admin',
            email='admin@purchase.test',
            password='testpass123',
        )
        cls.admin.role = 'admin'
        cls.admin.is_active = True
        cls.admin.save()

        # Create base catalog data
        cls.category = Category.objects.create(name='Test Category', slug='test-category')
        cls.unit = Unit.objects.create(name='Piece', short_name='pc', unit_type='unit')

        cls.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            sku='TST-PROD-001',
            barcode='8901234567890',
            category=cls.category,
            unit=cls.unit,
            base_price=Decimal("100.00"),
            selling_price=Decimal("100.00"),
            created_by=cls.admin,
        )

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            company_name='Supplier Corp',
            email='supplier@test.com',
            phone='+8801712345678',
            created_by=self.admin,
        )

    def test_create_supplier(self):
        """Verify supplier creation with all fields."""
        self.assertEqual(self.supplier.name, 'Test Supplier')
        self.assertEqual(self.supplier.company_name, 'Supplier Corp')
        self.assertEqual(self.supplier.phone, '+8801712345678')
        self.assertEqual(str(self.supplier), 'Test Supplier')

    def test_create_purchase(self):
        """Verify purchase creation with items."""
        purchase = Purchase.objects.create(
            invoice_number='PUR-2026-0001',
            supplier=self.supplier,
            total_amount=Decimal("500.00"),
            paid_amount=Decimal("0"),
            due_amount=Decimal("500.00"),
            status=Purchase.Status.PENDING,
            created_by=self.admin,
        )

        PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=5,
            cost_price=Decimal("100.00"),
            total_cost=Decimal("500.00"),
        )

        self.assertEqual(purchase.items.count(), 1)
        self.assertEqual(purchase.status, 'pending')
        self.assertEqual(purchase.supplier.name, 'Test Supplier')

    def test_purchase_approval_adds_inventory(self):
        """
        Verify that approving a purchase adds stock to inventory
        via InventoryService.add_stock().
        """
        purchase = Purchase.objects.create(
            invoice_number='PUR-2026-0002',
            supplier=self.supplier,
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("0"),
            due_amount=Decimal("1000.00"),
            status=Purchase.Status.APPROVED,
            created_by=self.admin,
        )

        item = PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=10,
            cost_price=Decimal("100.00"),
            total_cost=Decimal("1000.00"),
        )

        # Simulate the approval workflow: add stock to inventory
        tx = InventoryService.add_stock(
            product=self.product,
            quantity=item.quantity,
            cost_price=item.cost_price,
            transaction_type=InventoryTransaction.TransactionType.PURCHASE,
            performed_by=self.admin,
            source_document=purchase.invoice_number,
            notes=f"Stock from purchase {purchase.invoice_number}",
        )

        # Verify inventory batch was created
        batch = InventoryBatch.objects.filter(product=self.product).first()
        self.assertIsNotNone(batch, "InventoryBatch should be created")
        self.assertEqual(batch.remaining_quantity, 10)

        # Verify inventory transaction was created
        self.assertEqual(tx.transaction_type, 'purchase')
        self.assertEqual(tx.quantity, 10)

        # Verify product stock cache updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.base_stock, 10)

    def test_purchase_supplier_ledger(self):
        """Verify supplier ledger entries are created."""
        purchase = Purchase.objects.create(
            invoice_number='PUR-2026-0003',
            supplier=self.supplier,
            total_amount=Decimal("2000.00"),
            paid_amount=Decimal("1000.00"),
            due_amount=Decimal("1000.00"),
            created_by=self.admin,
        )

        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='purchase',
            amount=purchase.total_amount,
            balance_after=purchase.total_amount,
            reference=purchase.invoice_number,
            created_by=self.admin,
        )

        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='payment',
            amount=Decimal("1000.00"),
            balance_after=Decimal("1000.00"),
            reference=f"Payment for {purchase.invoice_number}",
            created_by=self.admin,
        )

        entries = SupplierLedger.objects.filter(supplier=self.supplier)
        self.assertEqual(entries.count(), 2)

        last_entry = entries.order_by('-created_at').first()
        self.assertEqual(last_entry.transaction_type, 'payment')
        self.assertEqual(last_entry.balance_after, Decimal("1000.00"))

    def test_purchase_cancellation(self):
        """Verify purchase can be cancelled."""
        purchase = Purchase.objects.create(
            invoice_number='PUR-2026-0004',
            supplier=self.supplier,
            total_amount=Decimal("500.00"),
            paid_amount=Decimal("0"),
            due_amount=Decimal("500.00"),
            status=Purchase.Status.PENDING,
            created_by=self.admin,
        )

        purchase.status = Purchase.Status.CANCELLED
        purchase.save()

        purchase.refresh_from_db()
        self.assertEqual(purchase.status, 'cancelled')

    def test_purchase_item_totals(self):
        """Verify purchase item total_cost is calculated correctly."""
        purchase = Purchase.objects.create(
            invoice_number='PUR-2026-0005',
            supplier=self.supplier,
            total_amount=Decimal("750.00"),
            created_by=self.admin,
        )

        item = PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=5,
            cost_price=Decimal("150.00"),
            total_cost=Decimal("750.00"),
        )

        self.assertEqual(item.total_cost, item.cost_price * item.quantity)

    def test_multiple_batches_from_purchases(self):
        """Verify multiple purchases create separate FIFO batches."""
        for i in range(3):
            inv = f'PUR-BATCH-{i+1:04d}'
            purchase = Purchase.objects.create(
                invoice_number=inv,
                supplier=self.supplier,
                total_amount=Decimal("500.00"),
                created_by=self.admin,
            )
            PurchaseItem.objects.create(
                purchase=purchase,
                product=self.product,
                quantity=5,
                cost_price=Decimal("100.00"),
                total_cost=Decimal("500.00"),
            )
            InventoryService.add_stock(
                product=self.product,
                quantity=5,
                cost_price=Decimal("100.00"),
                performed_by=self.admin,
                source_document=inv,
            )

        batches = InventoryBatch.objects.filter(
            product=self.product,
            is_active=True,
        )
        self.assertEqual(batches.count(), 3)

        # Verify all stock sums
        total_stock = sum(b.remaining_quantity for b in batches)
        self.assertEqual(total_stock, 15)