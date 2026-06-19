# =============================================================================
# RETURN SERVICE
# =============================================================================
#
# Responsibilities:
# - Approve return requests
# - Inspect returned items
# - Create refund (via PaymentService)
# - Create exchange orders
# - Restock returned items (via InventoryService)
# - Record accounting entries for returns
# - Update customer ledger
#
# Dependencies:
# - ReturnRecord / ReturnItem / ReturnInspection models
# - OrderService (for exchange orders)
# - InventoryService (for restocking)
# - PaymentService (for refunds)
# - AccountingService (for financial entries)
# - CustomerService (for ledger/wallet updates)
# =============================================================================

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import (
    ReturnRecord,
    ReturnItem,
    ReturnInspection,
    ExchangeRequest,
    Order,
    Payment,
    InventoryTransaction,
)


class ReturnService:
    """Manages the return/exchange lifecycle."""

    @staticmethod
    @transaction.atomic
    def approve_return(
        return_record: ReturnRecord,
        approved_by=None,
    ) -> ReturnRecord:
        """
        Approve a return request.

        This sets the return to APPROVED status and records
        who approved it.

        Args:
            return_record: ReturnRecord to approve.
            approved_by: User approving the return.

        Returns:
            Updated ReturnRecord instance.

        Raises:
            ValueError: If return is not in PENDING status.
        """
        if return_record.status != ReturnRecord.Status.PENDING:
            raise ValueError(
                f"Cannot approve return in status '{return_record.status}'."
            )

        return_record.status = ReturnRecord.Status.APPROVED
        return_record.approved_by = approved_by
        return_record.approved_at = timezone.now()
        return_record.save()

        return return_record

    @staticmethod
    @transaction.atomic
    def inspect_return(
        return_item: ReturnItem,
        inspector,
        outcome: str,
        notes: str = "",
    ) -> ReturnInspection:
        """
        Inspect a returned item and record the outcome.

        Args:
            return_item: ReturnItem being inspected.
            inspector: User performing the inspection.
            outcome: One of 'resellable', 'damaged', 'rejected'.
            notes: Inspection notes.

        Returns:
            ReturnInspection instance.
        """
        inspection = ReturnInspection.objects.create(
            return_item=return_item,
            inspector=inspector,
            outcome=outcome,
            notes=notes,
        )

        # Auto-update return status if all items inspected
        return_record = return_item.return_record
        all_items = return_record.items.all()
        inspected_items = ReturnInspection.objects.filter(
            return_item__in=all_items,
        ).values_list('return_item_id', flat=True).distinct()

        if len(inspected_items) == all_items.count():
            return_record.status = ReturnRecord.Status.INSPECTING
            return_record.save(update_fields=['status'])

        return inspection

    @staticmethod
    @transaction.atomic
    def create_refund(
        return_record: ReturnRecord,
        refund_method: str = "original",
        created_by=None,
    ) -> dict:
        """
        Create a refund for an approved/completed return.

        If the original payment was cash (COD), creates a CashMovement
        entry to track the cash payout from the register.

        Args:
            return_record: Approved ReturnRecord to refund.
            refund_method: How to process the refund.
            created_by: User processing the refund.

        Returns:
            dict with 'refund_transaction' and 'payment_status'.

        Raises:
            ValueError: If return is not in approved/completed status.
        """
        if return_record.status not in (
            ReturnRecord.Status.APPROVED,
            ReturnRecord.Status.COMPLETED,
        ):
            raise ValueError(
                f"Cannot refund return in status '{return_record.status}'."
            )

        # Calculate refund amount
        total_refund = Decimal("0")
        for item in return_record.items.all():
            approved_qty = item.approved_quantity or item.quantity
            total_refund += item.refund_amount * approved_qty

        if total_refund <= 0:
            raise ValueError("Refund amount must be positive.")

        # Process refund through payment service
        from .payment_service import PaymentService
        payment = return_record.order.payments.filter(
            status=Payment.Status.CAPTURED,
        ).first()

        if not payment:
            raise ValueError(
                f"No captured payment found for order {return_record.order.order_number}."
            )

        refund = PaymentService.refund_payment(
            payment=payment,
            amount=total_refund,
            refund_reason=return_record.reason,
            refund_method=refund_method,
            created_by=created_by,
        )

        # For POS cash refunds, record a cash movement
        if payment.is_cod and return_record.order.shift:
            try:
                register = return_record.order.shift.cash_register
                if register:
                    from .register_service import RegisterService
                    RegisterService.record_cash_movement(
                        register=register,
                        shift=return_record.order.shift,
                        movement_type='cash_out',
                        amount=total_refund,
                        note=f"Refund for return #{return_record.id}",
                        reference=f"Return #{return_record.id} / Order {return_record.order.order_number}",
                        created_by=created_by,
                    )
            except Exception:
                # Non-critical: refund already processed, register update is secondary
                pass

        # Record accounting entry for refund
        from .accounting_service import AccountingService
        AccountingService.record_refund(
            order=return_record.order,
            refund_amount=total_refund,
            refund_reason=return_record.reason,
            created_by=created_by,
        )

        # Mark return as completed
        return_record.status = ReturnRecord.Status.COMPLETED
        return_record.save()

        return {
            'refund_transaction': refund,
            'total_refund': total_refund,
        }

    @staticmethod
    @transaction.atomic
    def restock_returned_items(
        return_record: ReturnRecord,
        performed_by=None,
    ) -> list:
        """
        Restock approved items from a return back into inventory.

        Only items with 'resellable' inspection outcome are restocked.

        Args:
            return_record: ReturnRecord containing items to restock.
            performed_by: User performing the restock.

        Returns:
            List of InventoryTransaction instances created.
        """
        from .inventory_service import InventoryService

        transactions = []
        for return_item in return_record.items.all():
            # Check inspection outcome
            inspection = return_item.inspections.first()
            if inspection and inspection.outcome != 'resellable':
                continue

            approved_qty = return_item.approved_quantity or return_item.quantity
            if approved_qty <= 0:
                continue

            # Determine cost price for restock valuation
            cost_price = return_item.order_item.cost_price or Decimal("0")

            tx = InventoryService.add_stock(
                product=return_item.product,
                quantity=approved_qty,
                cost_price=cost_price,
                transaction_type=InventoryTransaction.TransactionType.CUSTOMER_RETURN,
                variant=return_item.variant,
                performed_by=performed_by,
                source_document=f"Return #{return_record.id}",
                notes=f"Restock from return #{return_record.id}",
            )
            transactions.append(tx)

        return transactions

    @staticmethod
    @transaction.atomic
    def create_exchange(
        exchange_request: ExchangeRequest,
        created_by=None,
    ) -> Order:
        """
        Process an exchange request by creating a replacement order.

        The exchange creates a negative order item (for the returned
        product) and a positive order item (for the new product),
        with the balance handled as store credit or additional payment.

        Args:
            exchange_request: ExchangeRequest to process.
            created_by: User processing the exchange.

        Returns:
            Order instance for the exchange.
        """
        if exchange_request.status != ExchangeRequest.Status.APPROVED:
            raise ValueError(
                f"Cannot process exchange in status '{exchange_request.status}'."
            )

        # Calculate price difference
        old_item_price = exchange_request.old_variant.selling_price if exchange_request.old_variant else exchange_request.old_order_item.unit_price
        new_item_price = exchange_request.new_variant.selling_price if exchange_request.new_variant else old_item_price

        price_difference = new_item_price - old_item_price

        # Create exchange order
        from .order_service import OrderService

        exchange_order = OrderService.create_order(
            user=exchange_request.user,
            source=exchange_request.order.source,
            items_data=[
                {
                    'product': exchange_request.new_variant.product if exchange_request.new_variant else exchange_request.old_order_item.product,
                    'variant': exchange_request.new_variant,
                    'quantity': exchange_request.quantity,
                    'unit_price': new_item_price,
                    'total_price': new_item_price * exchange_request.quantity,
                },
            ],
            terminal=exchange_request.order.terminal,
            shift=exchange_request.order.shift,
            cashier=created_by,
            created_by=created_by,
        )

        # Mark exchange as completed
        exchange_request.status = ExchangeRequest.Status.COMPLETED
        exchange_request.save()

        return exchange_order