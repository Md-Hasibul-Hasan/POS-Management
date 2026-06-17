# =============================================================================
#  MARKETING: Campaign, Coupon, Banner, Store, Notifications
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model

from .common import BaseModel

User = get_user_model()


class Campaign(BaseModel):
    CAMPAIGN_TYPE_CHOICES = [('flash_sale','Flash Sale'),('seasonal','Seasonal'),('clearance','Clearance'),('custom','Custom')]
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    campaign_type = models.CharField(max_length=50, choices=CAMPAIGN_TYPE_CHOICES, default='custom')
    discount_type = models.CharField(max_length=20, choices=[('percentage','Percentage'),('fixed','Fixed')])
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_limit = models.IntegerField(default=0, null=True, blank=True)
    current_usage = models.IntegerField(default=0)
    max_usage_per_user = models.IntegerField(default=0, null=True, blank=True)
    applicable_products = models.ManyToManyField('Product', blank=True, related_name='campaigns')
    applicable_categories = models.ManyToManyField('Category', blank=True, related_name='campaigns')
    banner = models.ImageField(upload_to='campaigns/banners/', null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_campaigns')

    def __str__(self):
        return self.name

    @property
    def is_running(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and not self.is_deleted and self.start_date <= now <= self.end_date

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date <= self.start_date:
            raise ValidationError('End time must be after start time.')
        if self.discount_type == 'percentage' and self.discount_value > 100:
            raise ValidationError('Percentage discount cannot exceed 100.')
        if self.max_discount_amount is not None and self.max_discount_amount < 0:
            raise ValidationError('Max discount amount cannot be negative.')

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CouponGroup(models.TextChoices):
    CASHBACK = 'cashback', 'Cashback'; SHIPPING = 'shipping', 'Free Shipping'; PRODUCT_DISCOUNT = 'product_discount', 'Product Discount'


class CouponCategory(models.TextChoices):
    WELCOME = 'welcome', 'Welcome'; FLASH_SALE = 'flash_sale', 'Flash Sale'; SEASONAL = 'seasonal', 'Seasonal'; REFERRAL = 'referral', 'Referral'


class Coupon(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    coupon_category = models.CharField(max_length=20, choices=CouponCategory.choices, default=CouponCategory.FLASH_SALE)
    discount_type = models.CharField(max_length=20, choices=[('percentage','Percentage'),('fixed','Fixed')])
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    coupon_group = models.CharField(max_length=30, choices=CouponGroup.choices, default=CouponGroup.PRODUCT_DISCOUNT)
    stack_priority = models.IntegerField(default=0)
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    usage_limit = models.IntegerField(default=0, null=True, blank=True)
    current_usage = models.IntegerField(default=0)
    max_usage_per_user = models.IntegerField(default=0, null=True, blank=True)
    applicable_products = models.ManyToManyField('Product', blank=True)
    applicable_categories = models.ManyToManyField('Category', blank=True)
    applicable_users = models.ManyToManyField(User, blank=True)
    first_order_only = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_coupons')

    def __str__(self):
        return self.code

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.end_date

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date <= self.start_date:
            raise ValidationError('End time must be after start time.')
        if self.discount_type == 'percentage' and self.discount_value > 100:
            raise ValidationError('Percentage discount cannot exceed 100.')

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper().strip()
        super().save(*args, **kwargs)


class CouponUsage(BaseModel):
    COUPON_STATUS_CHOICES = [('applied','Applied'),('failed','Failed'),('expired','Expired')]
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True, related_name='coupon_usages')
    discount_applied = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=COUPON_STATUS_CHOICES, default='applied')
    coupon_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['coupon', 'order'], name='unique_coupon_per_order')]

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"


class Banner(BaseModel):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    mobile_image = models.ImageField(upload_to='banners/mobile/', null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    link_type = models.CharField(max_length=20, choices=[('product','Product'),('category','Category'),('campaign','Campaign'),('url','URL'),('none','None')], default='none')
    linked_product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='banners')
    linked_category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='banners')
    linked_campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='banners')
    button_url = models.URLField(blank=True, default='')
    button_text = models.CharField(max_length=100, blank=True, default='')
    sort_order = models.IntegerField(default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_popup = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_banners')

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.link_type == 'product' and not self.linked_product:
            raise ValidationError('Product link type requires a linked product.')
        if self.link_type == 'category' and not self.linked_category:
            raise ValidationError('Category link type requires a linked category.')
        if self.link_type == 'campaign' and not self.linked_campaign:
            raise ValidationError('Campaign link type requires a linked campaign.')
        if self.link_type == 'url' and not self.button_url:
            raise ValidationError('URL link type requires a button URL.')
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError('End time must be after start time.')


class StoreSettings(BaseModel):
    store_name = models.CharField(max_length=255)
    store_slug = models.SlugField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='store/logos/', null=True, blank=True)
    favicon = models.ImageField(upload_to='store/favicons/', null=True, blank=True)
    support_email = models.EmailField(max_length=255, null=True, blank=True)
    support_phone = models.CharField(max_length=50, null=True, blank=True)
    support_whatsapp = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    currency = models.CharField(max_length=10, default='BDT')
    timezone = models.CharField(max_length=50, default='Asia/Dhaka')
    default_language = models.CharField(max_length=20, default='en')
    facebook_url = models.URLField(null=True, blank=True)
    instagram_url = models.URLField(null=True, blank=True)
    youtube_url = models.URLField(null=True, blank=True)
    linkedin_url = models.URLField(null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    maintenance_mode = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Store Setting'
        verbose_name_plural = 'Store Settings'

    def __str__(self):
        return self.store_name


class NotificationTemplate(BaseModel):
    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=100)
    email_subject = models.CharField(max_length=255, null=True, blank=True)
    email_content = models.TextField(null=True, blank=True)
    sms_content = models.TextField(null=True, blank=True)
    push_content = models.TextField(null=True, blank=True)
    variables = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name


class Notification(BaseModel):
    class Type(models.TextChoices):
        LOW_STOCK = 'low_stock', 'Low Stock Alert'; OUT_OF_STOCK = 'out_of_stock', 'Out of Stock Alert'
        DAMAGE = 'damage', 'Damage Alert'; LOST = 'lost', 'Lost Inventory Alert'
        NEW_ORDER = 'new_order', 'New Order Alert'; RETURN_REQUEST = 'return_request', 'Return Request Alert'
    class DeliveryChannel(models.TextChoices):
        IN_APP = 'in_app', 'In App'; EMAIL = 'email', 'Email'; BOTH = 'both', 'Both'
    class DeliveryStatus(models.TextChoices):
        SENT = 'sent', 'Sent'; FAILED = 'failed', 'Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    delivery_channel = models.CharField(max_length=20, choices=DeliveryChannel.choices)
    delivery_status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.SENT)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.user.email}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_read and not self.read_at:
            raise ValidationError('Read notification must have a read timestamp.')
        if not self.is_read and self.read_at:
            raise ValidationError('Unread notification cannot have a read timestamp.')