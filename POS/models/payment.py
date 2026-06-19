# =============================================================================
#  PAYMENT: Gateway, Methods, Sessions, Transactions, Refund
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from .common import BaseModel

User = get_user_model()


class PaymentGateway(BaseModel):
    GATEWAY_TYPE_CHOICES = [
        ('card', 'Card Payment'),
        ('wallet', 'Digital Wallet'),
        ('bank_transfer', 'Bank Transfer'),
        ('bnpl', 'Buy Now Pay Later'),
    ]

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPE_CHOICES)
    supported_currencies = models.JSONField(default=list)
    supports_refund = models.BooleanField(default=True)
    supports_partial_refund = models.BooleanField(default=False)
    supports_webhook = models.BooleanField(default=True)
    supports_emi = models.BooleanField(default=False)
    supports_cod = models.BooleanField(default=False)
    configuration = models.JSONField(default=dict, blank=True)
    sandbox_configuration = models.JSONField(default=dict, blank=True)
    live_configuration = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PaymentMethod(BaseModel):
    PAYMENT_TYPE_CHOICES = [
        ('debit_card', 'Debit Card'),
        ('credit_card', 'Credit Card'),
        ('wallet', 'Digital Wallet'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
    ]

    gateway = models.ForeignKey(
        PaymentGateway, on_delete=models.CASCADE, related_name='payment_methods'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    icon = models.ImageField(upload_to='payment_icons/', null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class PaymentSession(BaseModel):
    SESSION_STATUS_CHOICES = [
        ('created', 'Created'),
        ('initiated', 'Initiated'),
        ('awaiting_response', 'Awaiting Response'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payment_sessions')
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.PROTECT)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=100, unique=True)
    gateway_session_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_url = models.URLField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    session_status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='created')
    expires_at = models.DateTimeField()
    raw_session_response = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='ck_paymentsession_amount_positive'
            ),
        ]

    def __str__(self):
        return self.session_key


class Payment(BaseModel):
    class Status(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        PROCESSING = 'processing', 'Processing'
        AUTHORIZED = 'authorized', 'Authorized'
        CAPTURED = 'captured', 'Captured'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    class PaymentChannel(models.TextChoices):
        CARD = 'card', 'Card'
        WALLET = 'wallet', 'Digital Wallet'
        BANK = 'bank', 'Bank Transfer'
        UPI = 'upi', 'UPI'
        COD = 'cod', 'Cash on Delivery'

    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name='payments'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='payments'
    )
    payment_session = models.ForeignKey(
        PaymentSession, on_delete=models.SET_NULL, null=True, blank=True
    )
    gateway = models.ForeignKey(
        PaymentGateway, on_delete=models.PROTECT, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INITIATED
    )
    payment_method = models.CharField(max_length=50)
    payment_channel = models.CharField(
        max_length=20, choices=PaymentChannel.choices, null=True, blank=True
    )
    payment_gateway = models.CharField(max_length=50, blank=True, default='')
    gateway_transaction_id = models.CharField(max_length=255, blank=True, default='')
    gateway_reference_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    mobile_banking_txn_id = models.CharField(max_length=255, blank=True, default='')
    bank_transaction_id = models.CharField(max_length=255, blank=True, default='')
    gateway_customer_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_order_id = models.CharField(max_length=255, null=True, blank=True)
    is_cod = models.BooleanField(default=False)
    cod_collected_at = models.DateTimeField(null=True, blank=True)
    is_emi = models.BooleanField(default=False)
    emi_months = models.IntegerField(null=True, blank=True)
    emi_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    emi_bank = models.CharField(max_length=255, blank=True, default='')
    card_type = models.CharField(max_length=50, blank=True, default='')
    card_brand = models.CharField(max_length=50, blank=True, default='')
    card_issuer = models.CharField(max_length=255, blank=True, default='')
    card_last_four = models.CharField(max_length=4, blank=True, default='')
    wallet_type = models.CharField(max_length=50, null=True, blank=True)
    fraud_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='low'
    )
    is_flagged = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_payments'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='idx_payment_created_at'),
        ]

    def __str__(self):
        return f"Payment {self.amount} - {self.status}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount <= 0:
            raise ValidationError('Payment amount must be positive.')
        if self.fraud_score and (self.fraud_score < 0 or self.fraud_score > 100):
            raise ValidationError('Fraud score must be between 0 and 100.')
        if self.is_cod and not self.cod_collected_at:
            raise ValidationError('COD collection timestamp is required.')


class RefundTransaction(BaseModel):
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='refunds'
    )
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name='refunds'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_method = models.CharField(max_length=50)
    refund_reason = models.TextField()
    gateway_refund_id = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund {self.amount} - {self.status}"


class PaymentEventLog(BaseModel):
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='event_logs'
    )
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']