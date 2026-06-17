# =============================================================================
#  ACCOUNTING, SECURITY & FRAUD
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from .common import BaseModel

User = get_user_model()


class AccountCategory(BaseModel):
    class CategoryType(models.TextChoices):
        INCOME = 'income', 'Income'; EXPENSE = 'expense', 'Expense'

    name = models.CharField(max_length=255, unique=True)
    category_type = models.CharField(max_length=20, choices=CategoryType.choices)
    description = models.TextField(blank=True, default='')
    is_system = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_account_categories')

    class Meta:
        verbose_name_plural = 'account categories'
        ordering = ['category_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.category_type})"


class AccountTransaction(BaseModel):
    transaction_date = models.DateField()
    category = models.ForeignKey(AccountCategory, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    description = models.TextField(blank=True, default='')
    reference_type = models.CharField(max_length=50, blank=True, default='')
    reference_id = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.category.name}: {self.amount}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount <= 0:
            raise ValidationError('Transaction amount must be positive.')


class TaxConfiguration(BaseModel):
    class TaxType(models.TextChoices):
        VAT = 'vat', 'VAT'; GST = 'gst', 'GST'; SALES_TAX = 'sales_tax', 'Sales Tax'; CUSTOM = 'custom', 'Custom'

    name = models.CharField(max_length=255)
    tax_type = models.CharField(max_length=20, choices=TaxType.choices)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    country = models.CharField(max_length=100)
    division = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    is_default = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    applies_to_products = models.BooleanField(default=True)
    applies_to_shipping = models.BooleanField(default=False)
    applies_to_digital = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tax_configs')

    class Meta:
        ordering = ['-priority']

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class FraudRule(BaseModel):
    class RuleType(models.TextChoices):
        IP = 'ip', 'IP'; DEVICE = 'device', 'Device'; ORDER = 'order', 'Order'; PAYMENT = 'payment', 'Payment'; CUSTOM = 'custom', 'Custom'

    name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    rule_config = models.JSONField()
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_fraud_rules')

    def __str__(self):
        return self.name


class IPBlacklist(BaseModel):
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(blank=True, default='')
    blocked_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_ip_blacklists')

    def __str__(self):
        return str(self.ip_address)

    @property
    def is_expired(self):
        return self.blocked_until is not None and timezone.now() > self.blocked_until


class AuditLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50)
    module = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True, default='')
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['module', 'object_id']),
            models.Index(fields=['action_type']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.module} ({self.created_at})"