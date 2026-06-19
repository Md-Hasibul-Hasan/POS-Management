from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal

from .models import (
    # Catalog
    Category, Brand, Unit, Tag, Attribute, AttributeValue, VariantAttribute,
    ProductImage, ProductVideo, ReviewImage, ProductFAQ, ProductReview,
    # Product
    Product, ProductVariant,
    # Customer
    CustomerProfile, CustomerGroup, CustomerLedger, Address, WalletTransaction,
    LoyaltyPoints, LoyaltyTransaction, Wishlist, CompareList,
    # Order
    Order, OrderItem, OrderStatusLog, OrderCoupon, Cart, CartItem,
    ReturnRecord, ReturnItem, ReturnInspection, ExchangeRequest, Shipment,
    # Payment
    PaymentGateway, PaymentMethod, PaymentSession, Payment,
    RefundTransaction, PaymentEventLog,
    # Marketing
    Campaign, Coupon, CouponUsage, Banner, StoreSettings,
    NotificationTemplate, Notification,
    # Inventory
    Supplier, SupplierLedger, Purchase, PurchaseItem, PurchasePayment,
    InventoryBatch, InventoryTransaction, StockReservation,
    DamageReport, LostInventory, StockAdjustment, SupplierReturn, StockAudit,
    # Geo
    Country, Division, District, Area, CourierProvider, ShippingZone, ShippingRate,
    # Accounting
    AccountCategory, AccountTransaction, TaxConfiguration, FraudRule,
    IPBlacklist, AuditLog,
    # POS Operations
    POSTerminal, POSShift, CashRegister, CashMovement,
)


# =============================================================================
#  INLINES
# =============================================================================

# --- Catalog Inlines ---

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_preview', 'alt_text', 'is_primary', 'sort_order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    fields = ('url', 'title', 'sort_order')


class ProductFAQInline(admin.TabularInline):
    model = ProductFAQ
    extra = 1
    fields = ('question', 'answer', 'sort_order')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    fields = ('user', 'rating', 'title', 'comment', 'moderation_status', 'is_verified_purchase')
    readonly_fields = ('user', 'rating', 'title', 'comment', 'is_verified_purchase')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class VariantAttributeInline(admin.TabularInline):
    model = VariantAttribute
    extra = 1
    fields = ('attribute_name', 'attribute_value')


# --- Product Inlines ---

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = (
        'name', 'sku', 'is_default', 'base_price', 'selling_price',
        'stock', 'reserved_stock', 'low_stock_threshold', 'image_preview',
    )
    readonly_fields = ('image_preview', 'selling_price')
    show_change_link = True

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"


# --- Order Inlines ---

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        'product', 'variant', 'quantity', 'unit_price', 'total_price',
        'discount_amount', 'tax_amount',
    )
    readonly_fields = ('product', 'variant', 'quantity', 'unit_price', 'total_price', 'discount_amount', 'tax_amount')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    fields = ('previous_status', 'new_status', 'changed_by', 'note', 'created_at')
    readonly_fields = ('previous_status', 'new_status', 'changed_by', 'note', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class OrderCouponInline(admin.TabularInline):
    model = OrderCoupon
    extra = 0
    fields = ('coupon', 'discount_applied')
    readonly_fields = ('coupon', 'discount_applied')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# --- Cart Inlines ---

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = (
        'product', 'variant', 'quantity', 'unit_price_snapshot',
        'discount_snapshot', 'selected_for_checkout',
    )
    readonly_fields = ('product', 'variant', 'quantity', 'unit_price_snapshot', 'discount_snapshot')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# --- Purchase Inlines ---

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = ('product', 'variant', 'quantity', 'cost_price', 'total_cost')
    readonly_fields = ('total_cost',)


class PurchasePaymentInline(admin.TabularInline):
    model = PurchasePayment
    extra = 0
    fields = ('amount', 'payment_date', 'payment_method', 'reference', 'notes')
    readonly_fields = ('payment_date',)


# --- Return Inlines ---

class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0
    fields = ('order_item', 'product', 'variant', 'quantity', 'approved_quantity', 'refund_amount')
    readonly_fields = ('order_item', 'product', 'variant', 'quantity', 'approved_quantity', 'refund_amount')

    def has_add_permission(self, request, obj=None):
        return False


class ReturnInspectionInline(admin.TabularInline):
    model = ReturnInspection
    extra = 0
    fields = ('inspector', 'outcome', 'notes')


# --- Inventory Inlines ---

class InventoryBatchInline(admin.TabularInline):
    model = InventoryBatch
    extra = 0
    fields = (
        'batch_number', 'cost_price', 'received_quantity', 'remaining_quantity',
        'purchase_date', 'expiry_date', 'is_active',
    )
    readonly_fields = ('received_quantity', 'remaining_quantity', 'purchase_date')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 0
    fields = (
        'transaction_type', 'quantity', 'previous_stock', 'new_stock',
        'source_type', 'notes', 'performed_by', 'created_at',
    )
    readonly_fields = (
        'transaction_type', 'quantity', 'previous_stock', 'new_stock',
        'source_type', 'notes', 'performed_by', 'created_at',
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# --- Geo Inlines ---

class DivisionInline(admin.TabularInline):
    model = Division
    extra = 1
    fields = ('name', 'code')


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    fields = ('name', 'code')


class AreaInline(admin.TabularInline):
    model = Area
    extra = 1
    fields = ('name', 'postal_code')


class ShippingRateInline(admin.TabularInline):
    model = ShippingRate
    extra = 1
    fields = ('shipping_zone', 'courier_provider', 'base_rate', 'per_kg_rate', 'estimated_days')


# --- Supplier Inlines ---

class SupplierLedgerInline(admin.TabularInline):
    model = SupplierLedger
    extra = 0
    fields = ('transaction_type', 'amount', 'balance_after', 'reference', 'notes', 'created_at')
    readonly_fields = ('transaction_type', 'amount', 'balance_after', 'reference', 'notes', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
#  ADMIN REGISTRATIONS
# =============================================================================


# =============================================================================
#  1. CATALOG ADMIN
# =============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'sort_order', 'image_preview', 'product_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order',)
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'slug', 'parent', 'description')}),
        (_('Media'), {'fields': ('image', 'image_preview')}),
        (_('Sorting'), {'fields': ('sort_order',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"
    image_preview.allow_tags = True

    def product_count(self, obj):
        count = obj.products.count()
        url = f"/admin/POS/product/?category__id__exact={obj.id}"
        return format_html('<a href="{}">{} Products</a>', url, count)
    product_count.short_description = "Products"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order', 'is_featured', 'product_count', 'logo_preview', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'is_featured')
    readonly_fields = ('logo_preview', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'slug', 'description', 'website')}),
        (_('Media'), {'fields': ('logo', 'logo_preview', 'banner')}),
        (_('SEO'), {'classes': ('collapse',), 'fields': ('meta_title', 'meta_description')}),
        (_('Settings'), {'fields': ('sort_order', 'is_featured')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:contain;border-radius:4px;" />',
                obj.logo.url
            )
        return "No Logo"
    logo_preview.short_description = "Logo"

    def product_count(self, obj):
        count = obj.products.count()
        url = f"/admin/POS/product/?brand__id__exact={obj.id}"
        return format_html('<a href="{}">{} Products</a>', url, count)
    product_count.short_description = "Products"


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'unit_type')
    list_filter = ('unit_type',)
    search_fields = ('name', 'short_name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'attribute_type', 'values_count')
    list_filter = ('attribute_type',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def values_count(self, obj):
        return obj.values.count()
    values_count.short_description = "Values"


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ('value', 'color_code', 'image', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'color_display', 'image_preview')
    list_filter = ('attribute',)
    search_fields = ('value',)
    readonly_fields = ('image_preview',)

    def color_display(self, obj):
        if obj.color_code:
            return format_html(
                '<span style="background:{};padding:2px 8px;border-radius:3px;color:#fff;">{}</span>',
                obj.color_code, obj.color_code
            )
        return "-"
    color_display.short_description = "Color"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title_short', 'moderation_status', 'is_verified_purchase', 'review_images_count', 'created_at')
    list_filter = ('moderation_status', 'rating', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__email', 'title', 'comment')
    list_editable = ('moderation_status',)
    readonly_fields = ('product', 'user', 'order_item', 'rating', 'title', 'comment', 'is_verified_purchase', 'created_at', 'updated_at')
    actions = ('approve_reviews', 'reject_reviews', 'reset_to_pending')
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Review Details'), {'fields': ('product', 'user', 'order_item', 'rating')}),
        (_('Content'), {'fields': ('title', 'comment')}),
        (_('Moderation'), {'fields': ('moderation_status', 'is_verified_purchase')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def title_short(self, obj):
        return obj.title[:50] if obj.title else "-"
    title_short.short_description = "Title"

    def review_images_count(self, obj):
        count = obj.images.count()
        return count
    review_images_count.short_description = "Images"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    @admin.action(description='Approve selected reviews')
    def approve_reviews(self, request, queryset):
        updated = queryset.update(moderation_status='approved')
        self.message_user(request, f'{updated} review(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected reviews')
    def reject_reviews(self, request, queryset):
        updated = queryset.update(moderation_status='rejected')
        self.message_user(request, f'{updated} review(s) rejected.', messages.SUCCESS)

    @admin.action(description='Reset selected reviews to pending')
    def reset_to_pending(self, request, queryset):
        updated = queryset.update(moderation_status='pending')
        self.message_user(request, f'{updated} review(s) reset to pending.', messages.SUCCESS)


@admin.register(ProductFAQ)
class ProductFAQAdmin(admin.ModelAdmin):
    list_display = ('product', 'question_short', 'sort_order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'question', 'answer')
    list_editable = ('sort_order',)


    def question_short(self, obj):
        return obj.question[:60]
    question_short.short_description = "Question"


# =============================================================================
#  2. PRODUCT ADMIN
# =============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'sku', 'category', 'brand',
        'base_price', 'selling_price', 'stock_status_badge',
        'status_badge', 'approval_badge', 'is_featured',
        'is_special', 'is_trending', 'has_variants',
        'available_stock_display', 'total_units_sold',
        'average_rating', 'created_by', 'created_at',
    )
    list_display_links = ('image_preview', 'name', 'sku')
    list_filter = (
        'status', 'approval_status', 'stock_status',
        'is_featured', 'is_special', 'is_trending',
        'is_preorder', 'is_digital', 'has_variants',
        'buy_one_get_one', 'category', 'brand',
        'created_at', 'updated_at',
    )
    search_fields = ('name', 'sku', 'barcode', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    save_on_top = True
    list_editable = ('is_featured', 'is_special', 'is_trending')

    readonly_fields = (
        'image_preview', 'selling_price', 'stock_status',
        'total_units_sold', 'total_revenue', 'average_rating',
        'total_reviews', 'available_stock_display',
        'created_at', 'updated_at',
    )

    fieldsets = (
        (_('Identification'), {
            'fields': ('name', 'slug', 'sku', 'barcode', 'description', 'short_description')
        }),
        (_('Media'), {
            'fields': ('image_preview',)
        }),
        (_('SEO'), {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        (_('Categorization'), {
            'fields': ('category', 'brand', 'unit', 'tags')
        }),
        (_('Pricing'), {
            'fields': ('base_price', 'purchase_price', 'selling_price', 'currency',
                       'discount_type', 'discount_value')
        }),
        (_('Inventory'), {
            'classes': ('collapse',),
            'fields': (
                'base_stock', 'reserved_stock', 'available_stock_display',
                'low_stock_threshold', 'reorder_level', 'stock_status',
                'stock_alert_enabled', 'inventory_tracking_enabled',
                'track_serial_number', 'track_batch',
            )
        }),
        (_('Physical Attributes'), {
            'classes': ('collapse',),
            'fields': ('weight', 'dimensions', 'shipping_class', 'logistic_category',
                       'requires_shipping')
        }),
        (_('Flags'), {
            'fields': (
                'has_variants', 'is_featured', 'is_special', 'is_trending',
                'is_preorder', 'is_digital', 'buy_one_get_one',
            )
        }),
        (_('Status'), {
            'fields': ('status', 'approval_status', 'is_approved', 'published_at')
        }),
        (_('Cached Counters'), {
            'classes': ('collapse',),
            'fields': (
                'total_units_sold', 'total_revenue',
                'average_rating', 'total_reviews'
            )
        }),
        (_('Ownership'), {
            'classes': ('collapse',),
            'fields': ('created_by',)
        }),
        (_('Timestamps'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )

    inlines = [ProductImageInline, ProductVideoInline, ProductFAQInline, ProductReviewInline, ProductVariantInline]

    actions = (
        'approve_products', 'reject_products',
        'publish_products', 'archive_products',
        'mark_featured', 'mark_special', 'mark_trending',
        'disable_flags',
    )

    def image_preview(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary and primary.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />',
                primary.image.url
            )
        if obj.images.exists():
            img = obj.images.first()
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />',
                img.image.url
            )
        return format_html('<span style="color:#999;">No Img</span>')
    image_preview.short_description = "Image"

    def stock_status_badge(self, obj):
        colors = {'in_stock': '#15803d', 'low_stock': '#b45309', 'out_stock': '#b91c1c'}
        color = colors.get(obj.stock_status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_stock_status_display()
        )
    stock_status_badge.short_description = "Stock"

    def status_badge(self, obj):
        colors = {'draft': '#6b7280', 'published': '#15803d', 'archived': '#b91c1c'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def approval_badge(self, obj):
        colors = {'pending': '#b45309', 'approved': '#15803d', 'rejected': '#b91c1c'}
        color = colors.get(obj.approval_status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_approval_status_display()
        )
    approval_badge.short_description = "Approval"

    def available_stock_display(self, obj):
        return obj.available_stock
    available_stock_display.short_description = "Available"

    @admin.action(description='Approve selected products')
    def approve_products(self, request, queryset):
        for product in queryset:
            product.approve()
        self.message_user(request, f'{queryset.count()} product(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected products')
    def reject_products(self, request, queryset):
        for product in queryset:
            product.reject()
        self.message_user(request, f'{queryset.count()} product(s) rejected.', messages.SUCCESS)

    @admin.action(description='Publish selected products')
    def publish_products(self, request, queryset):
        updated = queryset.update(
            status='published', published_at=timezone.now()
        )
        self.message_user(request, f'{updated} product(s) published.', messages.SUCCESS)

    @admin.action(description='Archive selected products')
    def archive_products(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} product(s) archived.', messages.SUCCESS)

    @admin.action(description='Mark as featured')
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} product(s) marked as featured.', messages.SUCCESS)

    @admin.action(description='Mark as special')
    def mark_special(self, request, queryset):
        updated = queryset.update(is_special=True)
        self.message_user(request, f'{updated} product(s) marked as special.', messages.SUCCESS)

    @admin.action(description='Mark as trending')
    def mark_trending(self, request, queryset):
        updated = queryset.update(is_trending=True)
        self.message_user(request, f'{updated} product(s) marked as trending.', messages.SUCCESS)

    @admin.action(description='Clear all flags (featured/special/trending)')
    def disable_flags(self, request, queryset):
        updated = queryset.update(is_featured=False, is_special=False, is_trending=False)
        self.message_user(request, f'Flags cleared for {updated} product(s).', messages.SUCCESS)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'product', 'sku', 'is_default',
        'base_price', 'selling_price', 'stock', 'reserved_stock',
        'available_stock', 'low_stock_threshold', 'created_at',
    )
    list_filter = ('is_default', 'product', 'created_at')
    search_fields = ('name', 'sku', 'barcode', 'product__name')
    readonly_fields = (
        'image_preview', 'selling_price', 'attribute_signature',
        'available_stock', 'created_at', 'updated_at',
    )
    fieldsets = (
        (_('Basic Info'), {'fields': ('product', 'name', 'slug', 'sku', 'barcode', 'is_default')}),
        (_('Pricing'), {'fields': ('base_price', 'purchase_price', 'selling_price', 'currency',
                                    'discount_type', 'discount_value')}),
        (_('Inventory'), {'fields': ('stock', 'reserved_stock', 'available_stock',
                                      'low_stock_threshold', 'reorder_level',
                                      'stock_alert_enabled')}),
        (_('Attributes'), {'fields': ('attribute_signature',)}),
        (_('Physical'), {'classes': ('collapse',), 'fields': ('weight', 'dimensions',
                                                               'shipping_class', 'logistic_category')}),
        (_('Media'), {'fields': ('image', 'image_preview')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    inlines = [VariantAttributeInline]
    actions = ('mark_as_default', 'clear_default')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"

    def available_stock(self, obj):
        return max(obj.stock - obj.reserved_stock, 0)
    available_stock.short_description = "Available"

    @admin.action(description='Mark selected as default variant')
    def mark_as_default(self, request, queryset):
        for variant in queryset:
            ProductVariant.objects.filter(product=variant.product, is_default=True).update(is_default=False)
            variant.is_default = True
            variant.save()
        self.message_user(request, f'{queryset.count()} variant(s) set as default.', messages.SUCCESS)

    @admin.action(description='Clear default status')
    def clear_default(self, request, queryset):
        updated = queryset.update(is_default=False)
        self.message_user(request, f'Default status cleared for {updated} variant(s).', messages.SUCCESS)


# =============================================================================
#  3. CUSTOMER ADMIN
# =============================================================================

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'customer_id', 'phone', 'group', 'total_orders',
        'total_spent', 'wallet_balance', 'loyalty_points',
        'referral_code', 'created_at',
    )
    list_filter = ('group', 'gender', 'created_at')
    search_fields = ('user__email', 'user__name', 'customer_id', 'phone', 'referral_code')
    readonly_fields = ('user', 'total_orders', 'total_spent', 'total_returns',
                       'wallet_balance', 'loyalty_points', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('user', 'customer_id', 'phone', 'date_of_birth', 'gender')}),
        (_('Group & Referral'), {'fields': ('group', 'default_address', 'referral_code', 'referred_by')}),
        (_('Statistics'), {'fields': ('total_orders', 'total_spent', 'total_returns',
                                       'wallet_balance', 'loyalty_points')}),
        (_('Notes'), {'fields': ('notes',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )


@admin.register(CustomerGroup)
class CustomerGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percentage', 'customer_count', 'created_at')
    list_editable = ('discount_percentage',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    def customer_count(self, obj):
        return obj.customers.count()
    customer_count.short_description = "Customers"


@admin.register(CustomerLedger)
class CustomerLedgerAdmin(admin.ModelAdmin):
    list_display = ('customer', 'transaction_type', 'amount', 'balance_after', 'reference', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('customer__email', 'reference', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('customer', 'transaction_type', 'amount', 'balance_after', 'reference', 'notes', 'created_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'address_line1', 'district', 'country', 'address_type', 'is_default', 'is_deleted')
    list_filter = ('address_type', 'is_default', 'is_deleted', 'country', 'district')
    search_fields = ('user__email', 'address_line1', 'address_line2', 'phone', 'full_name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('soft_delete_selected', 'restore_selected')

    @admin.action(description='Soft delete selected addresses')
    def soft_delete_selected(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} address(es) soft-deleted.', messages.SUCCESS)

    @admin.action(description='Restore selected addresses')
    def restore_selected(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f'{updated} address(es) restored.', messages.SUCCESS)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'balance_before', 'balance_after', 'status', 'reference', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__email', 'reference', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'transaction_type', 'amount', 'balance_before', 'balance_after', 'status', 'reference', 'notes', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'lifetime_earned', 'lifetime_redeemed')
    search_fields = ('user__email',)
    readonly_fields = ('user', 'balance', 'lifetime_earned', 'lifetime_redeemed')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'points', 'balance_before', 'balance_after', 'reference', 'expires_at', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__email', 'reference', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'transaction_type', 'points', 'balance_before', 'balance_after', 'reference', 'expires_at', 'notes', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)


@admin.register(CompareList)
class CompareListAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)


# =============================================================================
#  4. ORDER ADMIN
# =============================================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'invoice_number', 'user_email', 'source',
        'status_badge', 'payment_status_badge', 'fulfillment_status',
        'total_amount', 'currency', 'item_count',
        'is_flagged', 'fraud_score', 'created_at',
    )
    list_display_links = ('order_number', 'invoice_number')
    list_filter = (
        'status', 'payment_status', 'fulfillment_status', 'source',
        'is_flagged', 'risk_level', 'currency',
        'return_requested', 'exchange_requested',
        'created_at', 'confirmed_at', 'delivered_at',
    )
    search_fields = (
        'order_number', 'invoice_number', 'user__email',
        'user__name', 'shipping_address_snapshot',
        'ip_address',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    save_on_top = True
    readonly_fields = (
        'order_number', 'invoice_number', 'user', 'source',
        'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount',
        'total_amount', 'currency',
        'is_flagged', 'fraud_score', 'risk_level',
        'ip_address', 'device_info',
        'confirmed_at', 'delivered_at', 'cancelled_at', 'returned_at',
        'created_at', 'updated_at',
    )
    fieldsets = (
        (_('Order Identification'), {
            'fields': ('order_number', 'invoice_number', 'user', 'source',
                       'terminal', 'shift', 'cashier')
        }),
        (_('Status'), {
            'fields': ('status', 'payment_status', 'fulfillment_status')
        }),
        (_('Financial'), {
            'fields': (
                'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount',
                'total_amount', 'currency', 'gift_wrap_charge',
            )
        }),
        (_('Logistics'), {
            'classes': ('collapse',),
            'fields': (
                'shipping_address', 'billing_address',
                'logistic_delivery_type', 'logistic_pickup_id',
                'estimated_delivery_date', 'total_weight',
                'is_gift', 'gift_message',
            )
        }),
        (_('Fraud Detection'), {
            'classes': ('collapse',),
            'fields': ('ip_address', 'device_info', 'fraud_score', 'risk_level', 'is_flagged')
        }),
        (_('Returns & Exchanges'), {
            'classes': ('collapse',),
            'fields': ('return_requested', 'exchange_requested')
        }),
        (_('Notes'), {
            'fields': ('order_notes',)
        }),
        (_('Timestamps'), {
            'classes': ('collapse',),
            'fields': (
                'confirmed_at', 'delivered_at', 'cancelled_at', 'returned_at',
                'created_at', 'updated_at',
            )
        }),
    )
    inlines = [OrderItemInline, OrderStatusLogInline, OrderCouponInline]
    actions = (
        'confirm_orders', 'mark_processing', 'mark_shipped',
        'mark_delivered', 'cancel_orders',
        'flag_orders', 'unflag_orders',
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else "Guest"
    user_email.short_description = "User"
    user_email.admin_order_field = 'user__email'

    def status_badge(self, obj):
        colors = {
            'pending': '#b45309', 'confirmed': '#2563eb', 'processing': '#7c3aed',
            'shipped': '#0891b2', 'delivered': '#15803d', 'cancelled': '#b91c1c',
            'returned': '#be185d',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def payment_status_badge(self, obj):
        colors = {'unpaid': '#b91c1c', 'paid': '#15803d', 'failed': '#b45309', 'refunded': '#7c3aed'}
        color = colors.get(obj.payment_status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Payment"

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"

    @admin.action(description='Confirm selected orders')
    def confirm_orders(self, request, queryset):
        updated = queryset.update(
            status='confirmed', confirmed_at=timezone.now()
        )
        self.message_user(request, f'{updated} order(s) confirmed.', messages.SUCCESS)

    @admin.action(description='Mark as processing')
    def mark_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.', messages.SUCCESS)

    @admin.action(description='Mark as shipped')
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status='shipped', fulfillment_status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.', messages.SUCCESS)

    @admin.action(description='Mark as delivered')
    def mark_delivered(self, request, queryset):
        updated = queryset.update(
            status='delivered', fulfillment_status='delivered',
            delivered_at=timezone.now()
        )
        self.message_user(request, f'{updated} order(s) marked as delivered.', messages.SUCCESS)

    @admin.action(description='Cancel selected orders')
    def cancel_orders(self, request, queryset):
        updated = queryset.update(
            status='cancelled', cancelled_at=timezone.now()
        )
        self.message_user(request, f'{updated} order(s) cancelled.', messages.SUCCESS)

    @admin.action(description='Flag selected orders')
    def flag_orders(self, request, queryset):
        updated = queryset.update(is_flagged=True, risk_level='high')
        self.message_user(request, f'{updated} order(s) flagged.', messages.SUCCESS)

    @admin.action(description='Unflag selected orders')
    def unflag_orders(self, request, queryset):
        updated = queryset.update(is_flagged=False, risk_level='low')
        self.message_user(request, f'{updated} order(s) unflagged.', messages.SUCCESS)


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'previous_status', 'new_status', 'changed_by', 'note_short', 'created_at')
    list_filter = ('new_status', 'created_at')
    search_fields = ('order__order_number', 'note', 'changed_by__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('order', 'previous_status', 'new_status', 'changed_by', 'note', 'created_at')

    def note_short(self, obj):
        return obj.note[:60] if obj.note else "-"
    note_short.short_description = "Note"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'item_count', 'is_active', 'expires_at', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('user', 'subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"


@admin.register(ReturnRecord)
class ReturnRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'return_type', 'status_badge', 'reason_short', 'return_date', 'approved_by')
    list_filter = ('return_type', 'status', 'return_date')
    search_fields = ('order__order_number', 'user__email', 'reason', 'notes')
    date_hierarchy = 'return_date'
    readonly_fields = ('order', 'user', 'return_type', 'reason', 'return_date', 'created_at', 'updated_at')
    fieldsets = (
        (_('Return Info'), {'fields': ('order', 'user', 'return_type', 'reason')}),
        (_('Status'), {'fields': ('status', 'notes', 'approved_by', 'approved_at')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('return_date', 'created_at', 'updated_at')}),
    )
    inlines = [ReturnItemInline]
    actions = ('approve_returns', 'reject_returns', 'mark_inspecting', 'complete_returns')

    def status_badge(self, obj):
        colors = {'pending': '#b45309', 'approved': '#15803d', 'rejected': '#b91c1c',
                  'inspecting': '#7c3aed', 'completed': '#0891b2'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def reason_short(self, obj):
        return obj.reason[:50] if obj.reason else "-"
    reason_short.short_description = "Reason"

    @admin.action(description='Approve selected returns')
    def approve_returns(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(status='approved', approved_by=request.user, approved_at=now)
        self.message_user(request, f'{updated} return(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected returns')
    def reject_returns(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} return(s) rejected.', messages.SUCCESS)

    @admin.action(description='Mark as inspecting')
    def mark_inspecting(self, request, queryset):
        updated = queryset.update(status='inspecting')
        self.message_user(request, f'{updated} return(s) marked as inspecting.', messages.SUCCESS)

    @admin.action(description='Complete selected returns')
    def complete_returns(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} return(s) completed.', messages.SUCCESS)


@admin.register(ExchangeRequest)
class ExchangeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'old_variant', 'new_variant', 'quantity', 'status_badge', 'reason_short', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'user__email', 'reason', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('order', 'user', 'old_order_item', 'old_variant', 'new_variant', 'quantity', 'reason', 'created_at', 'updated_at')
    actions = ('approve_exchanges', 'reject_exchanges', 'complete_exchanges')

    def status_badge(self, obj):
        colors = {'pending': '#b45309', 'approved': '#15803d', 'rejected': '#b91c1c', 'completed': '#0891b2'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def reason_short(self, obj):
        return obj.reason[:50] if obj.reason else "-"
    reason_short.short_description = "Reason"

    @admin.action(description='Approve selected exchanges')
    def approve_exchanges(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} exchange(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected exchanges')
    def reject_exchanges(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} exchange(s) rejected.', messages.SUCCESS)

    @admin.action(description='Complete selected exchanges')
    def complete_exchanges(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} exchange(s) completed.', messages.SUCCESS)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order', 'courier_name', 'status_badge', 'pickup_requested_at', 'delivered_at', 'created_at')
    list_filter = ('status', 'courier_name', 'created_at')
    search_fields = ('tracking_number', 'order__order_number', 'courier_name', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'courier_response')
    fieldsets = (
        (_('Shipment Info'), {'fields': ('order', 'tracking_number', 'courier_name', 'status', 'notes')}),
        (_('Timeline'), {
            'fields': (
                'pickup_requested_at', 'picked_up_at', 'in_transit_at',
                'delivered_at', 'failed_at', 'returned_at',
            )
        }),
        (_('Courier Data'), {'classes': ('collapse',), 'fields': ('courier_response',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    actions = ('mark_picked_up', 'mark_in_transit', 'mark_delivered', 'mark_failed')

    def status_badge(self, obj):
        colors = {
            'pending': '#6b7280', 'pickup_requested': '#b45309', 'picked_up': '#7c3aed',
            'in_transit': '#0891b2', 'delivered': '#15803d', 'failed': '#b91c1c', 'returned': '#be185d',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    @admin.action(description='Mark as picked up')
    def mark_picked_up(self, request, queryset):
        updated = queryset.update(status='picked_up', picked_up_at=timezone.now())
        self.message_user(request, f'{updated} shipment(s) marked as picked up.', messages.SUCCESS)

    @admin.action(description='Mark as in transit')
    def mark_in_transit(self, request, queryset):
        updated = queryset.update(status='in_transit', in_transit_at=timezone.now())
        self.message_user(request, f'{updated} shipment(s) marked as in transit.', messages.SUCCESS)

    @admin.action(description='Mark as delivered')
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f'{updated} shipment(s) marked as delivered.', messages.SUCCESS)

    @admin.action(description='Mark as failed')
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed', failed_at=timezone.now())
        self.message_user(request, f'{updated} shipment(s) marked as failed.', messages.SUCCESS)


# =============================================================================
#  5. PAYMENT ADMIN
# =============================================================================

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'gateway_type', 'is_active',
        'supports_refund', 'supports_webhook', 'supports_emi', 'supports_cod',
    )
    list_filter = ('gateway_type', 'is_active', 'supports_refund', 'supports_webhook')
    search_fields = ('name', 'code')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'code', 'gateway_type', 'is_active')}),
        (_('Capabilities'), {'fields': (
            'supported_currencies', 'supports_refund', 'supports_partial_refund',
            'supports_webhook', 'supports_emi', 'supports_cod',
        )}),
        (_('Configuration'), {'fields': ('configuration', 'sandbox_configuration', 'live_configuration')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'gateway', 'payment_type', 'processing_fee', 'sort_order', 'is_active')
    list_filter = ('payment_type', 'is_active', 'gateway')
    search_fields = ('name', 'code')
    list_editable = ('sort_order', 'is_active')


@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'order', 'gateway', 'amount', 'currency', 'session_status', 'expires_at', 'created_at')
    list_filter = ('session_status', 'currency', 'created_at')
    search_fields = ('session_key', 'order__order_number', 'gateway_session_id')
    readonly_fields = ('order', 'gateway', 'payment_method', 'session_key', 'amount', 'currency',
                       'session_status', 'expires_at', 'raw_session_response', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'order', 'user', 'amount', 'currency', 'status_badge',
        'payment_method', 'payment_channel', 'payment_gateway',
        'gateway_transaction_id_short', 'is_cod', 'is_flagged',
        'fraud_score', 'paid_at', 'created_at',
    )
    list_filter = (
        'status', 'payment_channel', 'payment_method', 'is_cod',
        'is_emi', 'is_flagged', 'risk_level', 'currency',
        'created_at', 'paid_at',
    )
    search_fields = (
        'order__order_number', 'user__email', 'gateway_transaction_id',
        'gateway_reference_id', 'mobile_banking_txn_id',
        'bank_transaction_id', 'notes',
    )
    date_hierarchy = 'created_at'
    readonly_fields = (
        'order', 'user', 'payment_session', 'gateway', 'amount', 'currency',
        'status', 'payment_method', 'payment_channel', 'payment_gateway',
        'gateway_transaction_id', 'gateway_reference_id', 'is_cod',
        'cod_collected_at', 'fraud_score', 'risk_level', 'is_flagged',
        'paid_at', 'created_at', 'updated_at',
    )
    fieldsets = (
        (_('Payment Info'), {'fields': ('order', 'user', 'amount', 'currency', 'status')}),
        (_('Gateway'), {'fields': (
            'payment_session', 'gateway', 'payment_method', 'payment_channel',
            'payment_gateway', 'gateway_transaction_id', 'gateway_reference_id',
        )}),
        (_('Transaction IDs'), {'fields': ('mobile_banking_txn_id', 'bank_transaction_id')}),
        (_('Card Details'), {'classes': ('collapse',), 'fields': (
            'card_type', 'card_brand', 'card_issuer', 'card_last_four',
        )}),
        (_('EMI'), {'classes': ('collapse',), 'fields': ('is_emi', 'emi_months', 'emi_amount', 'emi_bank')}),
        (_('COD'), {'classes': ('collapse',), 'fields': ('is_cod', 'cod_collected_at')}),
        (_('Fraud'), {'classes': ('collapse',), 'fields': ('fraud_score', 'risk_level', 'is_flagged')}),
        (_('Notes'), {'fields': ('notes',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('paid_at', 'created_at', 'updated_at')}),
    )
    actions = (
        'mark_captured', 'mark_failed', 'mark_refunded',
        'flag_payments', 'unflag_payments',
    )

    def status_badge(self, obj):
        colors = {
            'initiated': '#6b7280', 'processing': '#7c3aed',
            'authorized': '#0891b2', 'captured': '#15803d',
            'failed': '#b91c1c', 'refunded': '#b45309',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def gateway_transaction_id_short(self, obj):
        return obj.gateway_transaction_id[:30] if obj.gateway_transaction_id else "-"
    gateway_transaction_id_short.short_description = "Gateway TXN ID"

    @admin.action(description='Mark as captured')
    def mark_captured(self, request, queryset):
        updated = queryset.update(status='captured', paid_at=timezone.now())
        self.message_user(request, f'{updated} payment(s) marked as captured.', messages.SUCCESS)

    @admin.action(description='Mark as failed')
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.', messages.SUCCESS)

    @admin.action(description='Mark as refunded')
    def mark_refunded(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} payment(s) marked as refunded.', messages.SUCCESS)

    @admin.action(description='Flag selected payments')
    def flag_payments(self, request, queryset):
        updated = queryset.update(is_flagged=True, risk_level='high')
        self.message_user(request, f'{updated} payment(s) flagged.', messages.SUCCESS)

    @admin.action(description='Unflag selected payments')
    def unflag_payments(self, request, queryset):
        updated = queryset.update(is_flagged=False, risk_level='low')
        self.message_user(request, f'{updated} payment(s) unflagged.', messages.SUCCESS)


@admin.register(RefundTransaction)
class RefundTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'order', 'amount', 'refund_method', 'status_badge', 'refunded_at', 'created_at')
    list_filter = ('status', 'refund_method', 'created_at')
    search_fields = ('payment__gateway_transaction_id', 'order__order_number', 'refund_reason', 'gateway_refund_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('payment', 'order', 'amount', 'refund_method', 'refund_reason',
                       'gateway_refund_id', 'status', 'refunded_at', 'failure_reason', 'created_by', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def status_badge(self, obj):
        colors = {'pending': '#b45309', 'completed': '#15803d', 'failed': '#b91c1c'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"


@admin.register(PaymentEventLog)
class PaymentEventLogAdmin(admin.ModelAdmin):
    list_display = ('payment', 'event_type', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('payment__gateway_transaction_id', 'event_type', 'ip_address')
    date_hierarchy = 'created_at'
    readonly_fields = ('payment', 'event_type', 'event_data', 'ip_address', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# =============================================================================
#  6. MARKETING ADMIN
# =============================================================================

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'campaign_type', 'discount_type', 'discount_value',
        'max_discount_amount', 'is_running_status', 'is_active',
        'is_featured', 'priority', 'current_usage', 'usage_limit',
        'start_date', 'end_date', 'created_at',
    )
    list_filter = ('campaign_type', 'discount_type', 'is_active', 'is_featured', 'start_date', 'end_date')
    search_fields = ('name', 'slug', 'description')
    date_hierarchy = 'start_date'
    list_editable = ('is_active', 'is_featured', 'priority')
    readonly_fields = ('current_usage', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'slug', 'description', 'campaign_type')}),
        (_('Discount'), {'fields': ('discount_type', 'discount_value', 'max_discount_amount')}),
        (_('Schedule'), {'fields': ('start_date', 'end_date')}),
        (_('Usage Limits'), {'fields': ('usage_limit', 'current_usage', 'max_usage_per_user')}),
        (_('Applicability'), {'fields': ('applicable_products', 'applicable_categories')}),
        (_('Display'), {'fields': ('banner', 'priority', 'is_featured')}),
        (_('Settings'), {'fields': ('is_active',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    actions = ('activate_campaigns', 'deactivate_campaigns', 'reset_usage')

    def is_running_status(self, obj):
        if obj.is_running:
            return format_html('<span style="color:#15803d;font-weight:600;">Running</span>')
        return format_html('<span style="color:#b91c1c;font-weight:600;">Stopped</span>')
    is_running_status.short_description = "Running"

    @admin.action(description='Activate selected campaigns')
    def activate_campaigns(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} campaign(s) activated.', messages.SUCCESS)

    @admin.action(description='Deactivate selected campaigns')
    def deactivate_campaigns(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} campaign(s) deactivated.', messages.SUCCESS)

    @admin.action(description='Reset usage counter')
    def reset_usage(self, request, queryset):
        updated = queryset.update(current_usage=0)
        self.message_user(request, f'Usage counter reset for {updated} campaign(s).', messages.SUCCESS)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'title', 'coupon_category', 'coupon_group',
        'discount_type', 'discount_value', 'max_discount_amount',
        'min_order_amount', 'stack_priority',
        'current_usage', 'usage_limit',
        'is_expired_status', 'is_active',
        'start_date', 'end_date', 'created_at',
    )
    list_filter = (
        'coupon_category', 'coupon_group', 'discount_type',
        'is_active', 'first_order_only', 'start_date', 'end_date',
    )
    search_fields = ('code', 'title', 'description')
    date_hierarchy = 'start_date'
    list_editable = ('is_active', 'stack_priority')
    readonly_fields = ('current_usage', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('code', 'title', 'description', 'coupon_category', 'coupon_group')}),
        (_('Discount'), {'fields': ('discount_type', 'discount_value', 'max_discount_amount', 'min_order_amount')}),
        (_('Schedule'), {'fields': ('start_date', 'end_date')}),
        (_('Usage Limits'), {'fields': ('usage_limit', 'current_usage', 'max_usage_per_user', 'stack_priority')}),
        (_('Applicability'), {'fields': ('applicable_products', 'applicable_categories', 'applicable_users', 'first_order_only')}),
        (_('Settings'), {'fields': ('is_active',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    actions = ('activate_coupons', 'deactivate_coupons', 'reset_usage')

    def is_expired_status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color:#b91c1c;font-weight:600;">Expired</span>')
        return format_html('<span style="color:#15803d;font-weight:600;">Active</span>')
    is_expired_status.short_description = "Status"

    @admin.action(description='Activate selected coupons')
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} coupon(s) activated.', messages.SUCCESS)

    @admin.action(description='Deactivate selected coupons')
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} coupon(s) deactivated.', messages.SUCCESS)

    @admin.action(description='Reset usage counter')
    def reset_usage(self, request, queryset):
        updated = queryset.update(current_usage=0)
        self.message_user(request, f'Usage counter reset for {updated} coupon(s).', messages.SUCCESS)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'order', 'discount_applied', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('coupon__code', 'user__email', 'order__order_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('coupon', 'user', 'order', 'discount_applied', 'status', 'coupon_snapshot', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'link_type', 'image_preview', 'sort_order',
        'is_active', 'is_popup', 'start_date', 'end_date', 'created_at',
    )
    list_filter = ('link_type', 'is_active', 'is_popup', 'start_date', 'end_date')
    search_fields = ('title', 'short_description')
    list_editable = ('sort_order', 'is_active', 'is_popup')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Info'), {'fields': ('title', 'short_description', 'image', 'image_preview', 'mobile_image')}),
        (_('Link'), {'fields': (
            'link_type', 'linked_product', 'linked_category',
            'linked_campaign', 'button_url', 'button_text',
        )}),
        (_('Schedule'), {'fields': ('start_date', 'end_date')}),
        (_('Settings'), {'fields': ('sort_order', 'is_popup', 'is_active')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:100px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'store_slug', 'support_email', 'support_phone', 'currency', 'maintenance_mode', 'is_active')
    list_editable = ('maintenance_mode', 'is_active')
    search_fields = ('store_name', 'store_slug', 'support_email')
    fieldsets = (
        (_('Store Info'), {'fields': ('store_name', 'store_slug', 'logo', 'favicon')}),
        (_('Contact'), {'fields': ('support_email', 'support_phone', 'support_whatsapp', 'address')}),
        (_('Regional'), {'fields': ('currency', 'timezone', 'default_language')}),
        (_('Social'), {'classes': ('collapse',), 'fields': (
            'facebook_url', 'instagram_url', 'youtube_url', 'linkedin_url',
        )}),
        (_('SEO'), {'classes': ('collapse',), 'fields': ('meta_title', 'meta_description')}),
        (_('Settings'), {'fields': ('maintenance_mode', 'is_active')}),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'email_subject')
    list_filter = ('template_type',)
    search_fields = ('name', 'email_subject')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'delivery_channel', 'delivery_status', 'is_read', 'read_at', 'created_at')
    list_filter = ('notification_type', 'delivery_channel', 'delivery_status', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'notification_type', 'title', 'message', 'delivery_channel', 'delivery_status', 'created_at')
    actions = ('mark_as_read', 'mark_as_unread')

    @admin.action(description='Mark as read')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as read.', messages.SUCCESS)

    @admin.action(description='Mark as unread')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.', messages.SUCCESS)


# =============================================================================
#  7. INVENTORY ADMIN
# =============================================================================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_name', 'email', 'phone', 'purchase_count', 'created_at')
    search_fields = ('name', 'company_name', 'email', 'phone', 'tax_id')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SupplierLedgerInline]
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'company_name', 'email', 'phone', 'address')}),
        (_('Additional'), {'fields': ('tax_id', 'notes')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def purchase_count(self, obj):
        return obj.purchases.count()
    purchase_count.short_description = "Purchases"


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'supplier', 'total_amount', 'paid_amount',
        'due_amount', 'status_badge', 'approval_status_badge',
        'purchase_date', 'created_by', 'created_at',
    )
    list_filter = ('status', 'approval_status', 'purchase_date', 'created_at')
    search_fields = ('invoice_number', 'supplier__name', 'notes')
    date_hierarchy = 'purchase_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Purchase Info'), {'fields': ('invoice_number', 'supplier', 'purchase_date', 'notes')}),
        (_('Financial'), {'fields': ('total_amount', 'paid_amount', 'due_amount')}),
        (_('Status'), {'fields': ('status', 'approval_status')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    inlines = [PurchaseItemInline, PurchasePaymentInline]
    actions = (
        'approve_purchases', 'reject_purchases',
        'complete_purchases', 'cancel_purchases',
    )

    def status_badge(self, obj):
        colors = {'pending': '#b45309', 'approved': '#2563eb', 'completed': '#15803d', 'cancelled': '#b91c1c'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def approval_status_badge(self, obj):
        colors = {'pending': '#b45309', 'approved': '#15803d', 'rejected': '#b91c1c', 'cancelled': '#6b7280'}
        color = colors.get(obj.approval_status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_approval_status_display()
        )
    approval_status_badge.short_description = "Approval"

    def due_amount(self, obj):
        return obj.total_amount - obj.paid_amount
    due_amount.short_description = "Due"

    @admin.action(description='Approve selected purchases')
    def approve_purchases(self, request, queryset):
        updated = queryset.update(
            status='approved', approval_status='approved'
        )
        self.message_user(request, f'{updated} purchase(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected purchases')
    def reject_purchases(self, request, queryset):
        updated = queryset.update(
            status='cancelled', approval_status='rejected'
        )
        self.message_user(request, f'{updated} purchase(s) rejected.', messages.SUCCESS)

    @admin.action(description='Complete selected purchases')
    def complete_purchases(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} purchase(s) completed.', messages.SUCCESS)

    @admin.action(description='Cancel selected purchases')
    def cancel_purchases(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} purchase(s) cancelled.', messages.SUCCESS)


@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_number', 'product', 'variant', 'cost_price',
        'received_quantity', 'remaining_quantity', 'purchase_date',
        'expiry_date', 'is_active', 'created_at',
    )
    list_filter = ('is_active', 'purchase_date', 'expiry_date')
    search_fields = ('batch_number', 'product__name', 'product__sku')
    date_hierarchy = 'purchase_date'
    readonly_fields = ('received_quantity', 'remaining_quantity', 'created_at', 'updated_at')
    list_editable = ('is_active',)
    actions = ('deactivate_batches', 'activate_batches')

    @admin.action(description='Deactivate selected batches')
    def deactivate_batches(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} batch(es) deactivated.', messages.SUCCESS)

    @admin.action(description='Activate selected batches')
    def activate_batches(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} batch(es) activated.', messages.SUCCESS)


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_type', 'product', 'variant', 'quantity',
        'previous_stock', 'new_stock', 'source_type',
        'source_document', 'performed_by', 'is_reversed',
        'created_at',
    )
    list_filter = ('transaction_type', 'source_type', 'is_reversed', 'created_at')
    search_fields = (
        'product__name', 'product__sku', 'source_document',
        'notes', 'performed_by__email',
    )
    date_hierarchy = 'created_at'
    readonly_fields = (
        'transaction_type', 'product', 'variant', 'batch', 'quantity',
        'previous_stock', 'new_stock', 'source_type', 'source_document',
        'reference_id', 'notes', 'performed_by', 'is_reversed',
        'reversed_transaction', 'reversal_reason', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'variant', 'user', 'quantity', 'status', 'reservation_source', 'expires_at', 'created_at')
    list_filter = ('status', 'reservation_source', 'created_at')
    search_fields = ('product__name', 'user__email', 'order__order_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('product', 'variant', 'order', 'cart_item', 'user', 'quantity', 'status', 'reservation_source', 'checkout_token', 'expires_at', 'created_at')
    actions = ('release_reservations',)

    @admin.action(description='Release selected reservations')
    def release_reservations(self, request, queryset):
        updated = queryset.update(status='released', released_at=timezone.now())
        self.message_user(request, f'{updated} reservation(s) released.', messages.SUCCESS)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant', 'quantity', 'reason', 'damage_date', 'reported_by', 'created_at')
    list_filter = ('damage_date', 'created_at')
    search_fields = ('product__name', 'reason', 'notes')
    date_hierarchy = 'damage_date'
    readonly_fields = ('product', 'variant', 'quantity', 'reason', 'notes', 'reported_by', 'damage_date', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LostInventory)
class LostInventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant', 'quantity', 'reason', 'lost_date', 'reported_by', 'created_at')
    list_filter = ('lost_date', 'created_at')
    search_fields = ('product__name', 'reason', 'notes')
    date_hierarchy = 'lost_date'
    readonly_fields = ('product', 'variant', 'quantity', 'reason', 'notes', 'reported_by', 'lost_date', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant', 'quantity', 'previous_stock', 'new_stock', 'reason', 'adjusted_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'reason', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('product', 'variant', 'quantity', 'previous_stock', 'new_stock', 'reason', 'notes', 'adjusted_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SupplierReturn)
class SupplierReturnAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'purchase', 'product', 'variant', 'quantity', 'reason', 'return_date', 'returned_by', 'created_at')
    list_filter = ('return_date', 'created_at')
    search_fields = ('supplier__name', 'product__name', 'reason', 'notes')
    date_hierarchy = 'return_date'
    readonly_fields = ('supplier', 'purchase', 'product', 'variant', 'batch', 'quantity', 'reason', 'notes', 'returned_by', 'return_date', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StockAudit)
class StockAuditAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'variant', 'system_stock', 'physical_stock',
        'variance', 'variance_display', 'status_badge',
        'audited_by', 'audit_date', 'created_at',
    )
    list_filter = ('status', 'audit_date')
    search_fields = ('product__name', 'notes', 'audited_by__email')
    date_hierarchy = 'audit_date'
    readonly_fields = ('product', 'variant', 'system_stock', 'physical_stock', 'variance', 'audited_by', 'audit_date', 'created_at')
    fieldsets = (
        (_('Audit Info'), {'fields': ('product', 'variant', 'status')}),
        (_('Stock Comparison'), {'fields': ('system_stock', 'physical_stock', 'variance')}),
        (_('Details'), {'fields': ('notes', 'audited_by', 'audit_date')}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    actions = ('approve_audits', 'schedule_audits', 'start_audits')

    def variance_display(self, obj):
        if obj.variance > 0:
            return format_html('<span style="color:#b91c1c;font-weight:600;">+{}</span>', obj.variance)
        elif obj.variance < 0:
            return format_html('<span style="color:#15803d;font-weight:600;">{}</span>', obj.variance)
        return format_html('<span style="color:#6b7280;">0</span>')
    variance_display.short_description = "Variance"

    def status_badge(self, obj):
        colors = {'scheduled': '#6b7280', 'in_progress': '#7c3aed', 'completed': '#0891b2', 'approved': '#15803d'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    @admin.action(description='Approve selected audits')
    def approve_audits(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} audit(s) approved.', messages.SUCCESS)

    @admin.action(description='Mark as scheduled')
    def schedule_audits(self, request, queryset):
        updated = queryset.update(status='scheduled')
        self.message_user(request, f'{updated} audit(s) scheduled.', messages.SUCCESS)

    @admin.action(description='Mark as in progress')
    def start_audits(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} audit(s) marked as in progress.', messages.SUCCESS)


# =============================================================================
#  8. GEO ADMIN
# =============================================================================

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code', 'division_count')
    search_fields = ('name', 'iso_code')
    inlines = [DivisionInline]

    def division_count(self, obj):
        return obj.divisions.count()
    division_count.short_description = "Divisions"


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country', 'district_count')
    list_filter = ('country',)
    search_fields = ('name', 'code')
    inlines = [DistrictInline]

    def district_count(self, obj):
        return obj.districts.count()
    district_count.short_description = "Districts"


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'division', 'area_count')
    list_filter = ('division', 'division__country')
    search_fields = ('name', 'code')
    inlines = [AreaInline]

    def area_count(self, obj):
        return obj.areas.count()
    area_count.short_description = "Areas"


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'postal_code', 'district')
    list_filter = ('district', 'district__division')
    search_fields = ('name', 'postal_code')


@admin.register(CourierProvider)
class CourierProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'area_count', 'estimated_delivery_days', 'created_at')
    search_fields = ('name', 'code')
    filter_horizontal = ('areas', 'districts')
    inlines = [ShippingRateInline]

    def area_count(self, obj):
        return obj.areas.count()
    area_count.short_description = "Areas"


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ('shipping_zone', 'courier_provider', 'base_rate', 'per_kg_rate', 'estimated_days')
    list_filter = ('shipping_zone', 'courier_provider')
    search_fields = ('shipping_zone__name', 'courier_provider__name')
    list_editable = ('base_rate', 'per_kg_rate')


# =============================================================================
#  9. ACCOUNTING ADMIN
# =============================================================================

@admin.register(AccountCategory)
class AccountCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'is_system', 'created_at')
    list_filter = ('category_type', 'is_system')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AccountTransaction)
class AccountTransactionAdmin(admin.ModelAdmin):
    list_display = ('category', 'description_short', 'amount', 'currency', 'reference_type', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('description', 'reference_type', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def description_short(self, obj):
        return obj.description[:60] if obj.description else "-"
    description_short.short_description = "Description"


@admin.register(TaxConfiguration)
class TaxConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'tax_type', 'is_active', 'is_default')
    list_filter = ('is_active', 'is_default', 'tax_type')
    search_fields = ('name',)
    list_editable = ('percentage', 'is_active', 'is_default')


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'risk_score', 'is_active', 'created_at')
    list_filter = ('rule_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Rule Info'), {'fields': ('name', 'description', 'rule_type', 'risk_score')}),
        (_('Conditions'), {'fields': ('rule_config',)}),
        (_('Action'), {'fields': ('action', 'action_value')}),
        (_('Settings'), {'fields': ('is_active',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )


@admin.register(IPBlacklist)
class IPBlacklistAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'reason', 'is_active', 'blocked_until', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('ip_address', 'reason')
    readonly_fields = ('created_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'module', 'object_id', 'ip_address', 'created_at')
    list_filter = ('action_type', 'module', 'created_at')
    search_fields = ('user__email', 'action_type', 'module', 'object_id', 'ip_address', 'object_repr')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action_type', 'module', 'object_id', 'object_repr', 'old_data', 'new_data', 'ip_address', 'user_agent', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# =============================================================================
#  12. POS OPERATIONS ADMIN
# =============================================================================

@admin.register(POSTerminal)
class POSTerminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'terminal_code', 'location', 'is_active', 'shift_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'terminal_code', 'location')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Terminal Info'), {'fields': ('name', 'terminal_code', 'location')}),
        (_('Status'), {'fields': ('is_active',)}),
        (_('Ownership'), {'fields': ('created_by',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def shift_count(self, obj):
        return obj.shifts.count()
    shift_count.short_description = "Shifts"


@admin.register(POSShift)
class POSShiftAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'terminal', 'cashier_name', 'status_badge',
        'opening_time', 'closing_time', 'total_sales_amount',
        'total_orders', 'order_count',
    )
    list_filter = ('status', 'terminal', 'opening_time')
    search_fields = ('terminal__name', 'cashier__email', 'cashier__name')
    date_hierarchy = 'opening_time'
    readonly_fields = (
        'total_sales_amount', 'total_orders', 'opening_time',
        'closing_time', 'created_at', 'updated_at',
    )
    fieldsets = (
        (_('Shift Info'), {'fields': ('terminal', 'cashier')}),
        (_('Timings'), {'fields': ('opening_time', 'closing_time', 'status')}),
        (_('Notes'), {'fields': ('opening_note', 'closing_note')}),
        (_('Totals'), {'fields': ('total_sales_amount', 'total_orders')}),
        (_('Ownership'), {'fields': ('created_by',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    actions = ('close_selected_shifts',)

    def cashier_name(self, obj):
        return obj.cashier.get_full_name() or obj.cashier.username
    cashier_name.short_description = "Cashier"
    cashier_name.admin_order_field = 'cashier'

    def status_badge(self, obj):
        colors = {'open': '#15803d', 'closed': '#6b7280', 'paused': '#b45309'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def order_count(self, obj):
        return obj.orders.count()
    order_count.short_description = "Orders"

    @admin.action(description='Close selected shifts')
    def close_selected_shifts(self, request, queryset):
        for shift in queryset.filter(status='open'):
            shift.close(closing_note=f"Closed by admin: {request.user}")
        self.message_user(request, f'{queryset.count()} shift(s) closed.', messages.SUCCESS)


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'terminal', 'shift_link', 'status_badge',
        'opening_balance', 'expected_closing_balance',
        'actual_closing_balance', 'discrepancy_display',
        'opened_by_name', 'opened_at',
    )
    list_filter = ('status', 'terminal', 'opened_at')
    search_fields = ('terminal__name', 'shift__id')
    date_hierarchy = 'opened_at'
    readonly_fields = (
        'opening_balance', 'expected_closing_balance',
        'opened_at', 'closed_at', 'created_at', 'updated_at',
    )
    fieldsets = (
        (_('Register Info'), {'fields': ('terminal', 'shift')}),
        (_('Balances'), {'fields': (
            'opening_balance', 'expected_closing_balance',
            'actual_closing_balance', 'status'
        )}),
        (_('Opening / Closing'), {'fields': (
            'opened_by', 'opened_at', 'closed_by', 'closed_at'
        )}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    actions = ('reconcile_selected', 'mark_disputed_selected')

    def shift_link(self, obj):
        url = f"/admin/POS/posshift/{obj.shift.id}/change/"
        return format_html('<a href="{}">Shift #{}</a>', url, obj.shift.id)
    shift_link.short_description = "Shift"

    def status_badge(self, obj):
        colors = {'open': '#15803d', 'closed': '#6b7280', 'reconciled': '#2563eb', 'disputed': '#b91c1c'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def discrepancy_display(self, obj):
        d = obj.discrepancy
        if d is None:
            return "-"
        color = '#15803d' if d == 0 else '#b91c1c'
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, d)
    discrepancy_display.short_description = "Discrepancy"

    def opened_by_name(self, obj):
        if obj.opened_by:
            return obj.opened_by.get_full_name() or obj.opened_by.username
        return "-"
    opened_by_name.short_description = "Opened By"
    opened_by_name.admin_order_field = 'opened_by'

    @admin.action(description='Reconcile selected registers')
    def reconcile_selected(self, request, queryset):
        for reg in queryset:
            reg.reconcile()
        self.message_user(request, f'{queryset.count()} register(s) reconciled.', messages.SUCCESS)

    @admin.action(description='Mark selected as disputed')
    def mark_disputed_selected(self, request, queryset):
        for reg in queryset:
            reg.mark_disputed()
        self.message_user(request, f'{queryset.count()} register(s) marked as disputed.', messages.SUCCESS)


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = (
        'register', 'shift_link', 'movement_type_colored',
        'amount', 'note_short', 'reference', 'created_by', 'created_at',
    )
    list_filter = ('movement_type', 'created_at', 'register__terminal')
    search_fields = ('note', 'reference', 'register__terminal__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Movement Info'), {'fields': ('register', 'shift', 'movement_type', 'amount')}),
        (_('Details'), {'fields': ('note', 'reference')}),
        (_('Ownership'), {'fields': ('created_by',)}),
        (_('Timestamps'), {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def shift_link(self, obj):
        url = f"/admin/POS/posshift/{obj.shift.id}/change/"
        return format_html('<a href="{}">Shift #{}</a>', url, obj.shift.id)
    shift_link.short_description = "Shift"

    def movement_type_colored(self, obj):
        colors = {
            'cash_in': '#15803d', 'cash_out': '#b91c1c',
            'petty_cash': '#b45309', 'expense': '#7c3aed', 'adjustment': '#2563eb',
        }
        color = colors.get(obj.movement_type, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_movement_type_display()
        )
    movement_type_colored.short_description = "Type"

    def note_short(self, obj):
        return obj.note[:60] if obj.note else "-"
    note_short.short_description = "Note"
