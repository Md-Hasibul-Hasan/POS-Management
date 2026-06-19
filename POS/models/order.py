# =============================================================================
#  ORDER, CART, RETURNS, EXCHANGES, SHIPMENTS
# =============================================================================

from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

from .common import BaseModel

User = get_user_model()

# Forward references for POS integration (avoid circular imports)
# POSTerminal, POSShift — imported in clean() / methods where needed
# CashRegister — imported in services/payment_service.py or pos_service.py


# =============================================================================
#  ORDER
# =============================================================================

class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'; CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'; SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'; CANCELLED = 'cancelled', 'Cancelled'; RETURNED = 'returned', 'Returned'
    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'; PAID = 'paid', 'Paid'; FAILED = 'failed', 'Failed'; REFUNDED = 'refunded', 'Refunded'
    class FulfillmentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'; PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'; DELIVERED = 'delivered', 'Delivered'; CANCELLED = 'cancelled', 'Cancelled'
    class OrderSource(models.TextChoices):
        POS = 'pos', 'POS'; ONLINE = 'online', 'Online Store'; WEB = 'web', 'Web'; MOBILE = 'mobile', 'Mobile'; ADMIN = 'admin', 'Admin'; API = 'api', 'API'
    class LogisticDeliveryType(models.TextChoices):
        HOME_DELIVERY = 'home_delivery', 'Home Delivery'; PICKUP_POINT = 'pickup_point', 'Pickup Point'; CASH_ON_DELIVERY = 'cash_on_delivery', 'Cash on Delivery'

    order_number = models.CharField(max_length=255, unique=True)
    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    source = models.CharField(max_length=20, choices=OrderSource.choices, default='web')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    fulfillment_status = models.CharField(max_length=20, choices=FulfillmentStatus.choices, default=FulfillmentStatus.PENDING)
    order_notes = models.TextField(null=True, blank=True)
    coupons = models.ManyToManyField('Coupon', through='OrderCoupon', blank=True)
    shipping_address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='shipping_orders')
    billing_address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_orders')
    shipping_address_snapshot = models.JSONField(default=dict, blank=True)
    billing_address_snapshot = models.JSONField(default=dict, blank=True)
    applied_coupon_snapshots = models.JSONField(default=list, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='BDT')
    gift_wrap_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_gift = models.BooleanField(default=False)
    gift_message = models.TextField(blank=True, default='')
    total_weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    logistic_delivery_type = models.CharField(max_length=30, choices=LogisticDeliveryType.choices, null=True, blank=True)
    logistic_pickup_id = models.CharField(max_length=100, null=True, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.TextField(blank=True, default='')
    fraud_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_level = models.CharField(max_length=20, choices=[('low','Low'),('medium','Medium'),('high','High')], default='low')
    is_flagged = models.BooleanField(default=False)
    return_requested = models.BooleanField(default=False)
    exchange_requested = models.BooleanField(default=False)
    # ---- POS Integration ----
    terminal = models.ForeignKey(
        'POSTerminal', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders'
    )
    shift = models.ForeignKey(
        'POSShift', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders'
    )
    cashier = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pos_orders'
    )

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_orders')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='idx_order_created_at'),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email if self.user else 'Guest'}"

    def clean(self):
        from django.core.exceptions import ValidationError
        expected_total = self.subtotal + self.shipping_cost + self.tax_amount + self.gift_wrap_charge - self.discount_amount
        if abs(self.total_amount - expected_total) > Decimal("0.01"):
            raise ValidationError(f'Order total mismatch. Expected: {expected_total}, Got: {self.total_amount}')
        for field in ['subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount', 'gift_wrap_charge', 'total_weight', 'fraud_score']:
            if getattr(self, field) < 0:
                raise ValidationError(f'{field} cannot be negative.')
        if self.is_gift and not self.gift_message:
            raise ValidationError('Gift orders require a gift message.')


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, related_name='order_items')
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='BDT')
    tax_snapshot = models.JSONField(default=dict, blank=True)
    product_snapshot = models.JSONField(default=dict, blank=True)
    variant_snapshot = models.JSONField(default=dict, blank=True)
    campaign_snapshot = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name='ck_orderitem_quantity_gt_0')]

    def __str__(self):
        return f"{self.product.name if self.product else 'Deleted'} x {self.quantity}"


class OrderStatusLog(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    previous_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"


class OrderCoupon(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    coupon = models.ForeignKey('Coupon', on_delete=models.CASCADE)
    discount_applied = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['order', 'coupon'], name='unique_coupon_per_ordercoupon')]

    def __str__(self):
        return f"{self.coupon.code} in {self.order.order_number}"


# =============================================================================
#  CART
# =============================================================================

class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    coupons = models.ManyToManyField('Coupon', blank=True, related_name='carts')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(subtotal__gte=0), name='ck_cart_subtotal_non_negative'),
            models.CheckConstraint(condition=models.Q(tax_amount__gte=0), name='ck_cart_tax_non_negative'),
            models.CheckConstraint(condition=models.Q(discount_amount__gte=0), name='ck_cart_discount_non_negative'),
            models.CheckConstraint(condition=models.Q(total_amount__gte=0), name='ck_cart_total_non_negative'),
        ]

    def __str__(self):
        return f"Cart {self.id} - {self.user.email}"


class CartItem(BaseModel):
    DISCOUNT_SOURCE_CHOICES = [('campaign', 'Campaign'), ('product', 'Product'), ('variant', 'Variant'), ('coupon', 'Coupon')]

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    tax_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    applied_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    applied_discount_source = models.CharField(max_length=20, choices=DISCOUNT_SOURCE_CHOICES, null=True, blank=True)
    applied_campaign = models.ForeignKey('Campaign', on_delete=models.SET_NULL, null=True, blank=True)
    selected_for_checkout = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product', 'variant'], name='unique_cart_item_product_variant'),
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='ck_cartitem_quantity_positive'),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# =============================================================================
#  RETURNS & EXCHANGES
# =============================================================================

class ReturnRecord(BaseModel):
    class ReturnType(models.TextChoices):
        FULL = 'full', 'Full Return'; PARTIAL = 'partial', 'Partial Return'; EXCHANGE = 'exchange', 'Exchange'
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'; APPROVED = 'approved', 'Approved'; REJECTED = 'rejected', 'Rejected'
        INSPECTING = 'inspecting', 'Inspecting'; COMPLETED = 'completed', 'Completed'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='returns')
    return_type = models.CharField(max_length=20, choices=ReturnType.choices)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, default='')
    return_date = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_returns')
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-return_date']

    def __str__(self):
        return f"Return {self.id} - Order {self.order.order_number}"


class ReturnItem(BaseModel):
    return_record = models.ForeignKey(ReturnRecord, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    approved_quantity = models.IntegerField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class ReturnInspection(BaseModel):
    return_item = models.ForeignKey(ReturnItem, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    outcome = models.CharField(max_length=20, choices=[('resellable','Resellable'),('damaged','Damaged'),('rejected','Rejected')])
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Inspection: {self.outcome}"


class ExchangeRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'; APPROVED = 'approved', 'Approved'; REJECTED = 'rejected', 'Rejected'; COMPLETED = 'completed', 'Completed'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='exchanges')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exchanges')
    old_order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='exchanges_out')
    old_variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, related_name='exchanges_out')
    new_variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, related_name='exchanges_in')
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Exchange {self.id}: {self.old_variant} → {self.new_variant}"


class Shipment(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'; PICKUP_REQUESTED = 'pickup_requested', 'Pickup Requested'
        PICKED_UP = 'picked_up', 'Picked Up'; IN_TRANSIT = 'in_transit', 'In Transit'
        DELIVERED = 'delivered', 'Delivered'; FAILED = 'failed', 'Failed'; RETURNED = 'returned', 'Returned'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipments')
    tracking_number = models.CharField(max_length=255, unique=True)
    courier_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    pickup_requested_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    in_transit_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    courier_response = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_shipments')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.status}"