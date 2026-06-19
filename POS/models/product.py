# =============================================================================
#  PRODUCT & VARIANTS
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from hashlib import md5

from .common import BaseModel

User = get_user_model()


class Product(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class StockStatus(models.TextChoices):
        IN_STOCK = 'in_stock', 'In Stock'
        LOW_STOCK = 'low_stock', 'Low Stock'
        OUT_STOCK = 'out_stock', 'Out of Stock'

    # ---- Identification ----
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    sku = models.CharField(max_length=255, unique=True)
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    short_description = models.TextField(blank=True, default='')

    # ---- SEO ----
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)

    # ---- Relationships ----
    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products'
    )
    brand = models.ForeignKey(
        'Brand', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products'
    )
    unit = models.ForeignKey(
        'Unit', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products'
    )
    tags = models.ManyToManyField('Tag', blank=True, related_name='products')

    # ---- Ownership ----
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_products'
    )

    # ---- Flags ----
    has_variants = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_special = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_preorder = models.BooleanField(default=False)
    buy_one_get_one = models.BooleanField(default=False)
    inventory_tracking_enabled = models.BooleanField(default=True)

    # ---- Pricing ----
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='BDT')

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed'

    discount_type = models.CharField(
        max_length=20, choices=DiscountType.choices, null=True, blank=True
    )
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ---- Physical attributes ----
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)
    shipping_class = models.CharField(max_length=100, null=True, blank=True)
    logistic_category = models.CharField(max_length=100, null=True, blank=True)

    # ---- Stock (CACHE fields — SOURCE OF TRUTH is InventoryBatch + InventoryTransaction) ----
    # These fields are CACHED summaries only.
    # NEVER use them for real-time inventory calculations.
    # All stock mutations MUST go through InventoryTransaction.
    base_stock = models.IntegerField(default=0)
    reserved_stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    reorder_level = models.IntegerField(default=5)
    stock_status = models.CharField(
        max_length=20, choices=StockStatus.choices, default=StockStatus.IN_STOCK
    )
    stock_alert_enabled = models.BooleanField(default=False)

    # ---- Serial / Batch tracking ----
    track_serial_number = models.BooleanField(default=False)
    track_batch = models.BooleanField(default=False)

    # ---- Lifecycle ----
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    published_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    # ---- Digital product ----
    is_digital = models.BooleanField(default=False)
    requires_shipping = models.BooleanField(default=True)

    # ---- Cached counters ----
    total_units_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.IntegerField(default=0)

    # ---- Soft delete ----
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self._update_selling_price()
        self._update_stock_status()
        super().save(*args, **kwargs)

    def _update_selling_price(self):
        if self.discount_type == 'percentage':
            if self.discount_value > 100:
                self.discount_value = 0
            self.selling_price = self.base_price - (
                self.base_price * self.discount_value / 100
            )
        elif self.discount_type == 'fixed':
            if self.discount_value > self.base_price:
                self.discount_value = self.base_price
            self.selling_price = max(self.base_price - self.discount_value, 0)
        else:
            self.selling_price = self.base_price

    def _update_stock_status(self):
        available = self.available_stock
        if available <= 0:
            self.stock_status = self.StockStatus.OUT_STOCK
        elif available <= self.low_stock_threshold:
            self.stock_status = self.StockStatus.LOW_STOCK
        else:
            self.stock_status = self.StockStatus.IN_STOCK

    @property
    def available_stock(self):
        if self.has_variants:
            variants = self.variants.filter(is_deleted=False)
            total = sum(
                max(v.stock - v.reserved_stock, 0) for v in variants
            )
            return total
        return max(self.base_stock - self.reserved_stock, 0)

    def approve(self):
        self.is_approved = True
        self.approval_status = self.ApprovalStatus.APPROVED
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save()

    def reject(self):
        self.is_approved = False
        self.approval_status = self.ApprovalStatus.REJECTED
        self.save()

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.save()

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


class ProductVariant(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    sku = models.CharField(max_length=255, unique=True)
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    # ---- Ownership ----
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_product_variants'
    )

    # Pricing
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='BDT')

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed'

    discount_type = models.CharField(
        max_length=20, choices=DiscountType.choices, null=True, blank=True
    )
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Physical attributes
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)
    shipping_class = models.CharField(max_length=100, null=True, blank=True)
    logistic_category = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='products/variants/', null=True, blank=True)

    # Stock (CACHE field — SOURCE OF TRUTH is InventoryBatch + InventoryTransaction)
    # This field is a CACHED summary only.
    # NEVER use for real-time inventory calculations.
    stock = models.IntegerField(default=0)
    reserved_stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    reorder_level = models.IntegerField(default=5)
    stock_alert_enabled = models.BooleanField(default=False)

    # Attribute signature
    attribute_signature = models.CharField(
        max_length=64, unique=True, editable=False
    )

    # Track serial / batch
    track_serial_number = models.BooleanField(default=False)
    track_batch = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'slug'],
                name='unique_variant_slug_per_product'
            ),
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_default=True),
                name='unique_default_variant_per_product'
            ),
            models.CheckConstraint(
                condition=models.Q(reserved_stock__lte=models.F('stock')),
                name='ck_variant_reserved_lte_stock'
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        

        if not self.attribute_signature:
            self.attribute_signature = md5(
                f"{self.product_id}-{self.sku}".encode()
            ).hexdigest()

        self._update_selling_price()
        super().save(*args, **kwargs)

    def _update_selling_price(self):
        if self.discount_type == 'percentage':
            if self.discount_value > 100:
                self.discount_value = 0
            self.selling_price = self.base_price - (
                self.base_price * self.discount_value / 100
            )
        elif self.discount_type == 'fixed':
            if self.discount_value > self.base_price:
                self.discount_value = self.base_price
            self.selling_price = max(self.base_price - self.discount_value, 0)
        else:
            self.selling_price = self.base_price


