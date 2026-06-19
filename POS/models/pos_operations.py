# =============================================================================
#  POS OPERATIONS: Terminal, Shift, Cash Register, Cash Movement
# =============================================================================
#
# Production-ready POS operational models that integrate cleanly with the
# existing Order, Payment, InventoryTransaction, and AccountTransaction models.
#
# Integration Points:
#   - Order gets FK to POSTerminal, POSShift, cashier (User)
#   - CashRegister auto-updates on cash payment creation
#   - POS sales create: Order + OrderItem + InventoryTransaction(POS_SALE)
#                       + Payment + AccountTransaction
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

from .common import BaseModel

User = get_user_model()


# =============================================================================
#  POSTerminal
# =============================================================================

class POSTerminal(BaseModel):
    """Physical or virtual POS terminal / register station."""

    name = models.CharField(max_length=255)
    terminal_code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_pos_terminals'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.terminal_code})"


# =============================================================================
#  POSShift
# =============================================================================

class POSShift(BaseModel):
    """Tracks a cashier's shift at a specific terminal."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'
        PAUSED = 'paused', 'Paused'

    terminal = models.ForeignKey(
        POSTerminal, on_delete=models.CASCADE, related_name='shifts'
    )
    cashier = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='pos_shifts'
    )
    opening_time = models.DateTimeField(default=timezone.now)
    closing_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    opening_note = models.TextField(blank=True, default='')
    closing_note = models.TextField(blank=True, default='')
    total_sales_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    total_orders = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_pos_shifts'
    )

    class Meta:
        ordering = ['-opening_time']
        indexes = [
            models.Index(fields=['terminal', 'status']),
            models.Index(fields=['cashier', 'status']),
        ]

    def __str__(self):
        return (
            f"Shift {self.id} — {self.terminal.name} / {self.cashier.get_full_name() or self.cashier.username} "
            f"[{self.status}]"
        )

    def close(self, closing_note=''):
        """Close the shift, recording totals and end time."""
        from .order import Order

        self.closing_time = timezone.now()
        self.status = self.Status.CLOSED
        self.closing_note = closing_note

        # Aggregate sales for this shift
        shift_orders = Order.objects.filter(
            shift=self,
            source__in=['pos', 'online', 'web', 'mobile', 'admin', 'api'],
        )
        self.total_orders = shift_orders.count()
        total = shift_orders.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
        self.total_sales_amount = total
        self.save()

    def open_cash_register(self, opening_balance=0, opened_by=None):
        """Create or retrieve the CashRegister for this shift."""
        register, created = CashRegister.objects.get_or_create(
            shift=self,
            defaults={
                'terminal': self.terminal,
                'opening_balance': opening_balance,
                'expected_closing_balance': opening_balance,
                'actual_closing_balance': opening_balance,
                'status': CashRegister.Status.OPEN,
                'opened_by': opened_by,
                'opened_at': timezone.now(),
            }
        )
        return register

    def get_cash_register(self):
        """Return the CashRegister associated with this shift."""
        return getattr(self, 'cash_register', None)


# =============================================================================
#  CashRegister
# =============================================================================

class CashRegister(BaseModel):
    """Tracks physical cash in a terminal register for a shift.

    expected_closing_balance is calculated as:
        opening_balance + cash_sales + cash_in - cash_out - expenses - petty_cash

    actual_closing_balance is the physical count entered at shift close.
    The difference (actual - expected) indicates a discrepancy.
    """

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'
        RECONCILED = 'reconciled', 'Reconciled'
        DISPUTED = 'disputed', 'Disputed'

    terminal = models.ForeignKey(
        POSTerminal, on_delete=models.CASCADE, related_name='cash_registers'
    )
    shift = models.OneToOneField(
        POSShift, on_delete=models.CASCADE, related_name='cash_register'
    )
    opening_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    expected_closing_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    actual_closing_balance = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    opened_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='opened_cash_registers'
    )
    closed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='closed_cash_registers'
    )
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['terminal', 'status']),
        ]

    def __str__(self):
        return (
            f"Register {self.id} — {self.terminal.name} "
            f"[{self.status}] Bal: {self.expected_closing_balance}"
        )

    def close(self, actual_closing_balance, closed_by=None):
        """Close the register with physical count and compute discrepancy."""
        self.actual_closing_balance = actual_closing_balance
        self.closed_by = closed_by
        self.closed_at = timezone.now()
        self.status = self.Status.CLOSED
        self.save()

    def reconcile(self):
        """Mark register as reconciled (no discrepancy or discrepancy resolved)."""
        self.status = self.Status.RECONCILED
        self.save()

    def mark_disputed(self):
        """Flag register as having discrepancy that needs investigation."""
        self.status = self.Status.DISPUTED
        self.save()

    @property
    def discrepancy(self):
        """Difference between actual and expected closing balance."""
        if self.actual_closing_balance is None:
            return None
        return self.actual_closing_balance - self.expected_closing_balance

    @property
    def total_cash_sales(self):
        """Sum of cash payments recorded during this shift."""
        from .payment import Payment
        return Payment.objects.filter(
            order__shift=self.shift,
            payment_channel=Payment.PaymentChannel.COD,
            status__in=['captured', 'authorized'],
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def total_cash_movements_in(self):
        """Sum of cash_in movements."""
        return self.movements.filter(
            movement_type='cash_in'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def total_cash_movements_out(self):
        """Sum of cash_out, petty_cash, expense, and adjustment movements."""
        return self.movements.filter(
            movement_type__in=['cash_out', 'petty_cash', 'expense', 'adjustment']
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def recalculate_expected_balance(self):
        """Recalculate expected_closing_balance based on transactions."""
        self.expected_closing_balance = (
            self.opening_balance
            + self.total_cash_sales
            + self.total_cash_movements_in
            - self.total_cash_movements_out
        )
        self.save(update_fields=['expected_closing_balance'])
        return self.expected_closing_balance


# =============================================================================
#  CashMovement
# =============================================================================

class CashMovement(BaseModel):
    """Records any manual movement of cash in/out of the register.

    Types:
        cash_in     - Money added to register (e.g., starting float top-up)
        cash_out    - Money removed from register (e.g., cash pick-up)
        petty_cash  - Small expenses paid from register
        expense     - Business expense paid from register
        adjustment  - Manual correction to register balance
    """

    class MovementType(models.TextChoices):
        CASH_IN = 'cash_in', 'Cash In'
        CASH_OUT = 'cash_out', 'Cash Out'
        PETTY_CASH = 'petty_cash', 'Petty Cash'
        EXPENSE = 'expense', 'Expense'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    register = models.ForeignKey(
        CashRegister, on_delete=models.CASCADE, related_name='movements'
    )
    shift = models.ForeignKey(
        POSShift, on_delete=models.CASCADE, related_name='cash_movements'
    )
    movement_type = models.CharField(
        max_length=20, choices=MovementType.choices
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    note = models.TextField(blank=True, default='')
    reference = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_cash_movements'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['register', 'movement_type']),
            models.Index(fields=['shift']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.amount}"

    def save(self, *args, **kwargs):
        """Auto-update cash register expected balance on movement creation."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.register.recalculate_expected_balance()