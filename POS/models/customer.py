# =============================================================================
#  CUSTOMER: Profile, Groups, Ledger, Address, Wallet, Loyalty, Wishlist
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from .common import BaseModel, SoftDeleteManager, AllObjectsManager

User = get_user_model()


class CustomerProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    customer_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M','Male'),('F','Female'),('O','Other')], null=True, blank=True)
    group = models.ForeignKey('CustomerGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    default_address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_returns = models.IntegerField(default=0)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loyalty_points = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default='')

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(total_orders__gte=0), name='ck_customer_orders_non_negative'),
            models.CheckConstraint(condition=models.Q(total_spent__gte=0), name='ck_customer_spent_non_negative'),
        ]

    def __str__(self):
        return self.user.email


class CustomerGroup(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    description = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customer_groups')

    def __str__(self):
        return self.name


class CustomerLedger(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ledger_entries')
    transaction_type = models.CharField(max_length=20, choices=[('sale','Sale'),('payment','Payment'),('return','Return'),('refund','Refund'),('adjustment','Adjustment')])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_ledger_entries')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.email} - {self.transaction_type} - {self.amount}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=100, blank=True, default='')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default='')
    country = models.CharField(max_length=100)
    division = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    area = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    delivery_instructions = models.TextField(null=True, blank=True)
    address_type = models.CharField(max_length=20, choices=[('home','Home'),('work','Work'),('other','Other')], default='home')
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name_plural = 'addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.address_line1}, {self.district}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.latitude is not None and (self.latitude < -90 or self.latitude > 90):
            raise ValidationError('Latitude must be between -90 and 90.')
        if self.longitude is not None and (self.longitude < -180 or self.longitude > 180):
            raise ValidationError('Longitude must be between -180 and 180.')

    def soft_delete(self):
        self.is_deleted = True
        self.save()


class WalletTransaction(BaseModel):
    class TransactionType(models.TextChoices):
        CREDIT = 'credit', 'Credit'; DEBIT = 'debit', 'Debit'
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'; PENDING = 'pending', 'Pending'; FAILED = 'failed', 'Failed'; REVERSED = 'reversed', 'Reversed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    reference = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"


class LoyaltyPoints(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_points')
    balance = models.IntegerField(default=0)
    lifetime_earned = models.IntegerField(default=0)
    lifetime_redeemed = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.email}: {self.balance} points"


class LoyaltyTransaction(BaseModel):
    class TransactionType(models.TextChoices):
        EARNED = 'earned', 'Earned'; REDEEMED = 'redeemed', 'Redeemed'; EXPIRED = 'expired', 'Expired'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    points = models.IntegerField()
    balance_before = models.IntegerField()
    balance_after = models.IntegerField()
    reference = models.CharField(max_length=255, blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.points}"


class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='wishlisted_by')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_product')]

    def __str__(self):
        return f"{self.product.name} in {self.user.email}'s wishlist"


class CompareList(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compare_list_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='compared_by')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_compare_product')]

    def __str__(self):
        return f"{self.product.name} in comparison list"