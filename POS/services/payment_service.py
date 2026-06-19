# =============================================================================
# PAYMENT SERVICE
# =============================================================================
#
# Responsibilities:
# - Create payments (online + POS)
# - Verify payments
# - Process refunds
# - Handle payment gateways
# - Update payment status
# - Log payment events
# - Create payment sessions
# - Handle COD collection
# - Handle EMI payments
# - Log gateway events
# - Perform fraud validation
# - **Record cash payment on CashRegister (POS)**
# - **Create customer ledger entries for payments**
#
# Dependencies:
# - Payment model
# - CashRegister model (for cash payment tracking)
# - CustomerLedger model (for customer balance tracking)
# - AuditLog model
# =============================================================================

from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from ..models import (
    Payment,
    PaymentSession,
    RefundTransaction,
    PaymentEventLog,
    CashRegister,
    CustomerLedger,
    AuditLog,
)


class PaymentService:
    """Manages payment lifecycle — create, capture, refund, verify."""

    # ─────────────────────────────────────────────────────────────────
    #  PAYMENT CREATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_payment(
        order,
        user,
        amount: Decimal,
        payment_method: str,
        payment_channel: str = None,
        currency: str = "BDT",
        is_cod: bool = False,
        status: str = Payment.Status.CAPTURED,
        cash_register: CashRegister = None,
        created_by=None,
        **extra_fields,
    ) -> Payment:
        """
        Create a payment record and trigger side effects.

        For POS cash payments (is_cod=True), automatically updates
        the CashRegister expected_closing_balance.

        Args:
            order: Order being paid for.
            user: Customer/user making the payment.
            amount: Payment amount.
            payment_method: e.g., 'cash', 'card', 'mobile_banking'.
            payment_channel: e.g., 'cod', 'card', 'wallet'.
            currency: Currency code (default BDT).
            is_cod: True if cash-on-delivery / POS cash payment.
            status: Payment status. Default CAPTURED for POS.
            cash_register: CashRegister to update (required for POS cash).
            created_by: User who created this payment record.
            **extra_fields: Additional Payment model fields.

        Returns:
            Payment instance.

        Raises:
            ValueError: If cash_register required but not provided for COD.
        """
        if is_cod and cash_register is None:
            raise ValueError(
                "Cash register is required for COD/cash payments."
            )

        payment = Payment.objects.create(
            order=order,
            user=user,
            amount=amount,
            currency=currency,
            status=status,
            payment_method=payment_method,
            payment_channel=payment_channel or (
                Payment.PaymentChannel.COD if is_cod else None
            ),
            is_cod=is_cod,
            paid_at=timezone.now() if status == Payment.Status.CAPTURED else None,
            created_by=created_by,
            **extra_fields,
        )

        # ── Side effect: Update cash register for POS cash payments ──
        if is_cod and cash_register is not None:
            from .register_service import RegisterService
            RegisterService.record_cash_payment(
                register=cash_register,
                amount=amount,
            )

        # ── Side effect: Update customer ledger ──
        if user and user.is_authenticated:
            from .customer_service import CustomerService
            CustomerService.update_customer_ledger(
                customer=user,
                transaction_type='payment',
                amount=amount,
                reference=f"Order {order.order_number}",
                notes=f"Payment of {amount} {currency} via {payment_method}",
                created_by=created_by,
            )

        return payment

    # ─────────────────────────────────────────────────────────────────
    #  PAYMENT VERIFICATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def verify_payment(payment: Payment) -> Payment:
        """
        Verify and mark a payment as captured/authorized.

        For POS, payments are typically created as CAPTURED directly.
        For online, this verifies gateway response.

        Args:
            payment: Payment to verify.

        Returns:
            Updated Payment instance.
        """
        if payment.status not in (Payment.Status.INITIATED, Payment.Status.PROCESSING):
            raise ValueError(
                f"Cannot verify payment in status '{payment.status}'."
            )

        payment.status = Payment.Status.CAPTURED
        payment.paid_at = timezone.now()
        payment.save()

        PaymentEventLog.objects.create(
            payment=payment,
            event_type='payment_verified',
            event_data={'verified_at': timezone.now().isoformat()},
        )

        return payment

    # ─────────────────────────────────────────────────────────────────
    #  PAYMENT STATUS UPDATE
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_payment_status(
        payment: Payment,
        new_status: str,
        notes: str = "",
    ) -> Payment:
        """
        Update payment status and log the event.

        Args:
            payment: Payment to update.
            new_status: Target status value.
            notes: Optional notes.

        Returns:
            Updated Payment instance.

        Raises:
            ValueError: If the status transition is invalid.
        """
        valid_transitions = {
            Payment.Status.INITIATED: [Payment.Status.PROCESSING, Payment.Status.FAILED],
            Payment.Status.PROCESSING: [
                Payment.Status.AUTHORIZED,
                Payment.Status.CAPTURED,
                Payment.Status.FAILED,
            ],
            Payment.Status.AUTHORIZED: [Payment.Status.CAPTURED, Payment.Status.FAILED],
            Payment.Status.CAPTURED: [Payment.Status.REFUNDED],
        }

        allowed = valid_transitions.get(payment.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition payment from '{payment.status}' to '{new_status}'. "
                f"Allowed transitions: {allowed}"
            )

        old_status = payment.status
        payment.status = new_status
        if new_status == Payment.Status.CAPTURED:
            payment.paid_at = timezone.now()
        payment.save()

        PaymentEventLog.objects.create(
            payment=payment,
            event_type=f'status_change_{old_status}_to_{new_status}',
            event_data={
                'previous_status': old_status,
                'new_status': new_status,
                'notes': notes,
            },
        )

        return payment

    # ─────────────────────────────────────────────────────────────────
    #  REFUND
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def refund_payment(
        payment: Payment,
        amount: Decimal,
        refund_reason: str,
        refund_method: str = "original",
        created_by=None,
        restock_items: bool = False,
    ) -> RefundTransaction:
        """
        Process a refund for a payment.

        For POS cash payments, this does NOT modify the CashRegister
        (refunds are tracked separately via CashMovement).

        Args:
            payment: Payment to refund.
            amount: Refund amount.
            refund_reason: Why the refund is being processed.
            refund_method: How the refund is delivered.
            created_by: User processing the refund.

        Returns:
            RefundTransaction instance.

        Raises:
            ValueError: If refund amount exceeds payment amount.
        """
        if payment.status != Payment.Status.CAPTURED:
            raise ValueError(
                f"Cannot refund payment in status '{payment.status}'. "
                f"Only CAPTURED payments can be refunded."
            )

        # Calculate total already refunded
        total_refunded = payment.refunds.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal("0")

        if total_refunded + amount > payment.amount:
            raise ValueError(
                f"Refund amount {amount} exceeds remaining balance "
                f"({payment.amount - total_refunded})."
            )

        refund = RefundTransaction.objects.create(
            payment=payment,
            order=payment.order,
            amount=amount,
            refund_method=refund_method,
            refund_reason=refund_reason,
            status='completed',
            refunded_at=timezone.now(),
            created_by=created_by,
        )

        # If full refund, mark payment as refunded
        if total_refunded + amount >= payment.amount:
            payment.status = Payment.Status.REFUNDED
            payment.save()

        # Log event
        PaymentEventLog.objects.create(
            payment=payment,
            event_type='refund_processed',
            event_data={
                'refund_id': refund.id,
                'amount': str(amount),
                'reason': refund_reason,
            },
        )

        # Record customer ledger entry for refund
        if payment.user and payment.user.is_authenticated:
            from .customer_service import CustomerService
            CustomerService.update_customer_ledger(
                customer=payment.user,
                transaction_type='refund',
                amount=amount,
                reference=f"Refund for Order {payment.order.order_number}",
                notes=refund_reason,
                created_by=created_by,
            )

        # Restock inventory items if requested (full refund restocks all items)
        if restock_items:
            from .inventory_service import InventoryService
            from ..models import InventoryTransaction
            for item in payment.order.items.all():
                InventoryService.add_stock(
                    product=item.product,
                    quantity=item.quantity,
                    cost_price=item.cost_price or Decimal("0"),
                    transaction_type=InventoryTransaction.TransactionType.REFUND,
                    variant=item.variant,
                    performed_by=created_by,
                    source_document=f"Refund for {payment.order.order_number}",
                    notes=f"Auto-restock from refund: {refund_reason}",
                )

        return refund
