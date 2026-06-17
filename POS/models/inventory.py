# =============================================================================
#  INVENTORY & SUPPLY CHAIN MODELS
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from .common import BaseModel
from .product import Product, ProductVariant

User = get_user_model()


# =============================================================================
#  5. SUPPLIER
# =============================================================================

class Supplier(BaseModel):
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, default='')
    email = models.EmailField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=50)
    address = models.TextField(blank=True, default='')
    tax_id = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_suppliers'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierLedger(BaseModel):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='ledger_entries'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('purchase', 'Purchase'),
            ('payment', 'Payment'),
            ('return', 'Return'),
            ('adjustment', 'Adjustment'),
        ]
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.supplier.name} - {self.transaction_type} - {self.amount}"


# =============================================================================
#  6. PURCHASE
# =============================================================================

class Purchase(BaseModel):
    invoice_number = models.CharField(max_length=255, unique=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='purchases'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='purchases'
    )
    purchase_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, default='')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"Purchase {self.invoice_number} - {self.supplier.name}"


class PurchaseItem(BaseModel):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='purchase_items'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='purchase_items'
    )
    quantity = models.IntegerField()
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class PurchasePayment(BaseModel):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=50)
    reference = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.amount} for {self.purchase.invoice_number}"


# =============================================================================
#  7. INVENTORY BATCH (FIFO Source of Truth)
# =============================================================================

class InventoryBatch(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='batches'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='batches'
    )
    purchase_item = models.ForeignKey(
        PurchaseItem, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='inventory_batches'
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    received_quantity = models.IntegerField()
    remaining_quantity = models.IntegerField()
    purchase_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['purchase_date', 'id']

    def __str__(self):
        return (
            f"Batch {self.id}: {self.product.name} "
            f"({self.remaining_quantity}/{self.received_quantity})"
        )


# =============================================================================
#  8. INVENTORY TRANSACTION (Single Source of Truth)
# =============================================================================

class InventoryTransaction(BaseModel):
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        POS_SALE = 'pos_sale', 'POS Sale'
        ONLINE_SALE = 'online_sale', 'Online Sale'
        CUSTOMER_RETURN = 'customer_return', 'Customer Return'
        SUPPLIER_RETURN = 'supplier_return', 'Supplier Return'
        DAMAGE = 'damage', 'Damage'
        LOST = 'lost', 'Lost'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        RESERVATION = 'reservation', 'Reservation'
        RESERVATION_RELEASE = 'reservation_release', 'Reservation Release'
        REFUND = 'refund', 'Refund'

    class SourceType(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        ORDER = 'order', 'Order'
        RETURN = 'return', 'Return'
        SYSTEM = 'system', 'System'

    transaction_type = models.CharField(
        max_length=30, choices=TransactionType.choices
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='inventory_transactions'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='inventory_transactions'
    )
    batch = models.ForeignKey(
        InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions'
    )
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    source_type = models.CharField(
        max_length=20, choices=SourceType.choices, default=SourceType.MANUAL
    )
    source_document = models.CharField(max_length=255, blank=True, default='')
    reference_id = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_reversed = models.BooleanField(default=False)
    reversed_transaction = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reverse_entries'
    )
    reversal_reason = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = '+' if self.quantity > 0 else ''
        return f"{self.transaction_type}: {self.product.name} ({direction}{self.quantity})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity == 0:
            raise ValidationError('Transaction quantity cannot be zero.')
        if self.previous_stock < 0 or self.new_stock < 0:
            raise ValidationError('Stock values cannot be negative.')
        if self.variant and self.variant.product != self.product:
            raise ValidationError('Variant must belong to the specified product.')


# =============================================================================
#  9. STOCK RESERVATION
# =============================================================================

class StockReservation(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CONVERTED_TO_SALE = 'converted_to_sale', 'Converted To Sale'
        RELEASED = 'released', 'Released'
        EXPIRED = 'expired', 'Expired'

    class Source(models.TextChoices):
        CART = 'cart', 'Cart'
        CHECKOUT = 'checkout', 'Checkout'
        ADMIN = 'admin', 'Admin'

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reservations'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reservations'
    )
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name='reservations'
    )
    cart_item = models.ForeignKey(
        'CartItem', on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reservations'
    )
    quantity = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    reservation_source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.CART
    )
    checkout_token = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    expires_at = models.DateTimeField()
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reservation {self.id}: {self.product.name} x {self.quantity}"


# =============================================================================
#  10. DAMAGE, LOST, ADJUSTMENT, SUPPLIER RETURN
# =============================================================================

class DamageReport(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='damage_reports'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    reported_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    damage_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-damage_date']

    def __str__(self):
        return f"Damage: {self.product.name} x {self.quantity}"


class LostInventory(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='lost_records'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    reported_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    lost_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'lost inventory'
        ordering = ['-lost_date']

    def __str__(self):
        return f"Lost: {self.product.name} x {self.quantity}"


class StockAdjustment(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='adjustments'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    adjusted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = '+' if self.quantity > 0 else ''
        return f"Adjustment: {self.product.name} ({direction}{self.quantity})"


class SupplierReturn(BaseModel):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='returns'
    )
    purchase = models.ForeignKey(
        Purchase, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='supplier_returns'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='supplier_returns'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True
    )
    batch = models.ForeignKey(
        InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='supplier_returns'
    )
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    returned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    return_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-return_date']

    def __str__(self):
        return f"Supplier Return: {self.product.name} x {self.quantity}"


# =============================================================================
#  11. STOCK AUDIT
# =============================================================================

class StockAudit(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        APPROVED = 'approved', 'Approved'

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='audits'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True
    )
    system_stock = models.IntegerField()
    physical_stock = models.IntegerField()
    variance = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    notes = models.TextField(blank=True, default='')
    audited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audits'
    )
    audit_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-audit_date']

    def __str__(self):
        return f"Audit: {self.product.name} (variance: {self.variance})"