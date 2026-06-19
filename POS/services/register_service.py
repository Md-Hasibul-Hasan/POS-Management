# =============================================================================
# REGISTER SERVICE
# =============================================================================
#
# Responsibilities:
# - Open a cash register for a shift
# - Close a cash register with physical count
# - Recalculate expected balance from transactions
# - Reconcile register (discrepancy=0 or resolved)
# - Mark register as disputed
# - Record cash payment impact on register balance
#
# Dependencies:
# - CashRegister model
# - POSShift model
# - CashMovement model
# =============================================================================

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import CashRegister, CashMovement, POSShift


class RegisterService:
    """Manages cash register lifecycle — opening, closing, reconciliation."""

    @staticmethod
    @transaction.atomic
    def open_register(
        shift: POSShift,
        opening_balance: Decimal = Decimal("0"),
        opened_by=None,
    ) -> CashRegister:
        """
        Open a cash register for a shift.

        Args:
            shift: The POSShift this register belongs to.
            opening_balance: Starting cash in the drawer.
            opened_by: User who opened the register.

        Returns:
            CashRegister instance.

        Raises:
            ValueError: If a register already exists for this shift.
        """
        if hasattr(shift, 'cash_register') and shift.cash_register is not None:
            raise ValueError(f"Shift {shift.id} already has an open register.")

        register = CashRegister.objects.create(
            terminal=shift.terminal,
            shift=shift,
            opening_balance=opening_balance,
            expected_closing_balance=opening_balance,
            actual_closing_balance=opening_balance,
            status=CashRegister.Status.OPEN,
            opened_by=opened_by,
            opened_at=timezone.now(),
        )
        return register

    @staticmethod
    @transaction.atomic
    def close_register(
        register: CashRegister,
        actual_closing_balance: Decimal,
        closed_by=None,
    ) -> CashRegister:
        """
        Close a register with the physical cash count.

        The register's expected_closing_balance is recalculated first,
        then compared with the actual physical count.

        Args:
            register: CashRegister to close.
            actual_closing_balance: Physical cash counted.
            closed_by: User closing the register.

        Returns:
            Updated CashRegister instance.
        """
        if register.status == CashRegister.Status.CLOSED:
            raise ValueError(f"Register {register.id} is already closed.")

        # Recalculate expected balance before closing
        register.recalculate_expected_balance()

        # Refresh from DB after recalculation
        register.refresh_from_db()

        register.actual_closing_balance = actual_closing_balance
        register.closed_by = closed_by
        register.closed_at = timezone.now()
        register.status = CashRegister.Status.CLOSED
        register.save()

        return register

    @staticmethod
    @transaction.atomic
    def reconcile_register(register: CashRegister) -> CashRegister:
        """
        Mark register as reconciled (discrepancy accepted/resolved).

        Args:
            register: CashRegister to reconcile.

        Returns:
            Updated CashRegister instance.

        Raises:
            ValueError: If register is not in CLOSED status.
        """
        if register.status not in (CashRegister.Status.CLOSED, CashRegister.Status.DISPUTED):
            raise ValueError(
                f"Register {register.id} must be CLOSED or DISPUTED to reconcile. "
                f"Current status: {register.status}"
            )
        register.status = CashRegister.Status.RECONCILED
        register.save()
        return register

    @staticmethod
    @transaction.atomic
    def mark_disputed(register: CashRegister) -> CashRegister:
        """
        Flag register as having a discrepancy that needs investigation.

        Args:
            register: CashRegister to mark as disputed.

        Returns:
            Updated CashRegister instance.
        """
        register.status = CashRegister.Status.DISPUTED
        register.save()
        return register

    @staticmethod
    @transaction.atomic
    def record_cash_payment(register: CashRegister, amount: Decimal) -> CashRegister:
        """
        Record a cash payment against the register.

        This updates the expected_closing_balance incrementally.
        Called by PaymentService when a cash payment is captured.

        Args:
            register: CashRegister to update.
            amount: Cash payment amount received.

        Returns:
            Updated CashRegister instance.
        """
        if register.status != CashRegister.Status.OPEN:
            raise ValueError(
                f"Cannot record cash payment on a {register.status} register."
            )

        register.expected_closing_balance += amount
        register.save(update_fields=['expected_closing_balance'])
        return register

    @staticmethod
    @transaction.atomic
    def record_cash_movement(
        register: CashRegister,
        shift: POSShift,
        movement_type: str,
        amount: Decimal,
        note: str = "",
        reference: str = "",
        created_by=None,
    ) -> CashMovement:
        """
        Record a manual cash movement into/out of the register.

        This delegates to CashMovement.save() which auto-updates
        the register's expected_closing_balance.

        Args:
            register: CashRegister affected.
            shift: POSShift this movement belongs to.
            movement_type: One of cash_in, cash_out, petty_cash, expense, adjustment.
            amount: Amount of cash moved.
            note: Description of the movement.
            reference: Reference document (e.g., invoice, receipt).
            created_by: User who recorded the movement.

        Returns:
            CashMovement instance.
        """
        if register.status != CashRegister.Status.OPEN:
            raise ValueError(
                f"Cannot record cash movement on a {register.status} register."
            )

        movement = CashMovement.objects.create(
            register=register,
            shift=shift,
            movement_type=movement_type,
            amount=amount,
            note=note,
            reference=reference,
            created_by=created_by,
        )
        return movement