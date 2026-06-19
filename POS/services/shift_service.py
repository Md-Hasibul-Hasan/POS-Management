# =============================================================================
# SHIFT SERVICE
# =============================================================================
#
# Responsibilities:
# - Start a new shift for a cashier at a terminal
# - End an open shift with closing totals
# - Calculate shift sales amount from orders
# - Calculate shift order count
# - Calculate shift cash total
# - Validate no overlapping shifts for same cashier
#
# Dependencies:
# - POSShift model
# - POSTerminal model
# - RegisterService (for opening register on shift start)
# =============================================================================

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import POSShift, POSTerminal, CashRegister


class ShiftService:
    """Manages POS shift lifecycle — start, end, and aggregation."""

    @staticmethod
    @transaction.atomic
    def start_shift(
        terminal: POSTerminal,
        cashier,
        opening_note: str = "",
        opening_balance: Decimal = Decimal("0"),
        created_by=None,
    ) -> dict:
        """
        Start a new shift for a cashier at a terminal.

        Automatically opens a CashRegister for the shift.

        Args:
            terminal: POSTerminal where the shift operates.
            cashier: User who will operate the shift.
            opening_note: Optional note for shift start.
            opening_balance: Starting cash in the register drawer.
            created_by: User who created this shift (usually the cashier or manager).

        Returns:
            dict: {'shift': POSShift, 'register': CashRegister}

        Raises:
            ValueError: If cashier has an overlapping open shift.
        """
        # Prevent overlapping open shifts for same cashier
        existing_open = POSShift.objects.filter(
            cashier=cashier,
            status=POSShift.Status.OPEN,
        ).exists()
        if existing_open:
            raise ValueError(
                f"Cashier {cashier.get_username() or cashier.email} "
                f"already has an open shift. Close it first."
            )

        if not terminal.is_active:
            raise ValueError(f"Terminal '{terminal.name}' is not active.")

        # Create the shift
        shift = POSShift.objects.create(
            terminal=terminal,
            cashier=cashier,
            opening_time=timezone.now(),
            status=POSShift.Status.OPEN,
            opening_note=opening_note,
            created_by=created_by or cashier,
        )

        # Open a cash register for this shift
        from .register_service import RegisterService
        register = RegisterService.open_register(
            shift=shift,
            opening_balance=opening_balance,
            opened_by=cashier,
        )

        return {"shift": shift, "register": register}

    @staticmethod
    @transaction.atomic
    def end_shift(
        shift: POSShift,
        actual_closing_balance: Decimal,
        closing_note: str = "",
        closed_by=None,
    ) -> dict:
        """
        End an open shift: close the register, then close the shift.

        Args:
            shift: POSShift to close.
            actual_closing_balance: Physical cash counted in the register.
            closing_note: Optional note for shift end.
            closed_by: User closing the shift (usually the cashier or manager).

        Returns:
            dict: {
                'shift': POSShift (closed),
                'register': CashRegister (closed),
                'discrepancy': Decimal | None
            }
        """
        if shift.status != POSShift.Status.OPEN:
            raise ValueError(
                f"Shift {shift.id} is not open. Current status: {shift.status}"
            )

        # Close the register first
        register = shift.cash_register
        if register is None:
            raise ValueError(f"No cash register found for shift {shift.id}.")

        from .register_service import RegisterService
        register = RegisterService.close_register(
            register=register,
            actual_closing_balance=actual_closing_balance,
            closed_by=closed_by,
        )

        # Now close the shift (aggregates totals)
        shift.close(closing_note=closing_note)

        return {
            "shift": shift,
            "register": register,
            "discrepancy": register.discrepancy,
        }

    @staticmethod
    def calculate_shift_sales(shift: POSShift) -> Decimal:
        """
        Calculate total sales amount for a shift.

        Args:
            shift: POSShift to calculate for.

        Returns:
            Decimal total sales amount.
        """
        from django.db.models import Sum
        from ..models import Order

        result = Order.objects.filter(
            shift=shift,
        ).aggregate(total=Sum('total_amount'))

        return result['total'] or Decimal("0")

    @staticmethod
    def calculate_shift_orders(shift: POSShift) -> int:
        """
        Count the number of orders in a shift.

        Args:
            shift: POSShift to calculate for.

        Returns:
            int order count.
        """
        from ..models import Order

        return Order.objects.filter(shift=shift).count()

    @staticmethod
    def calculate_shift_cash(shift: POSShift) -> Decimal:
        """
        Calculate total cash sales for a shift.

        Args:
            shift: POSShift to calculate for.

        Returns:
            Decimal total cash amount.
        """
        from django.db.models import Sum
        from ..models import Order, Payment

        result = Payment.objects.filter(
            order__shift=shift,
            payment_channel=Payment.PaymentChannel.COD,
            status__in=['captured', 'authorized'],
        ).aggregate(total=Sum('amount'))

        return result['total'] or Decimal("0")