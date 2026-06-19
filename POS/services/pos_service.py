# =============================================================================
# POS SERVICE — Orchestrator
# =============================================================================
#
# This is the top-level coordinator for Point-of-Sale operations.
# It delegates to specialized services for each concern:
#
#   OrderService      → order + order items creation
#   PaymentService    → payment creation + cash register update
#   InventoryService  → stock deduction (FIFO)
#   AccountingService → financial entries
#   CustomerService   → customer ledger + walk-in creation
#   ShiftService      → shift lifecycle
#   RegisterService   → cash register lifecycle
#
# Responsibilities:
# - Open POS shift (delegates to ShiftService)
# - Close POS shift (delegates to ShiftService)
# - Create POS sale (orchestrates: Order → Payment → Inventory → Accounting)
# - Complete instant checkout workflow
# - Hold/resume POS sales (draft orders)
# - Generate POS invoices
# - Handle walk-in customer creation
# - Handle POS returns/exchanges (delegates to ReturnService)
#
# Main Methods:
#   create_pos_sale()    ← single atomic entry for completing a POS sale
#   hold_sale()
#   resume_sale()
#   generate_invoice()
#   create_walkin_customer()
#
# Usage Example:
#   result = POSService.create_pos_sale(
#       terminal=terminal,
#       shift=shift,
#       cashier=cashier,
#       customer=user,
#       items=[...],
#       payments=[...],
#   )
# =============================================================================

from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone

from ..models import (
    Order,
    OrderItem,
    POSTerminal,
    POSShift,
    CashRegister,
    Product,
    ProductVariant,
)


class POSService:
    """
    Top-level POS orchestrator.
    Coordinates all sub-services to complete a POS sale atomically.
    """

    # ─────────────────────────────────────────────────────────────────
    #  CREATE POS SALE (The Main Workflow)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_pos_sale(
        *,
        terminal: POSTerminal,
        shift: POSShift,
        cashier,
        customer,
        items: list,
        payments: list,
        order_notes: str = "",
        shipping_cost: Decimal = Decimal("0"),
        tax_amount: Decimal = Decimal("0"),
        currency: str = "BDT",
        discount_amount: Decimal = Decimal("0"),
        created_by=None,
    ) -> dict:
        """
        Complete an entire POS sale in one atomic transaction.

        Orchestration flow:
        1. Validate shift/register are open
        2. Calculate item prices (via PricingEngine)
        3. Create Order + OrderItems (via OrderService)
        4. Create Payments + update CashRegister (via PaymentService)
        5. Confirm order + deduct inventory (via OrderService + InventoryService)
        6. Record accounting entries (via AccountingService)
        7. Update customer ledger (via CustomerService)

        Args:
            terminal: POSTerminal where the sale occurs.
            shift: POSShift this sale belongs to.
            cashier: User operating the register.
            customer: Customer User (or walk-in anonymous user).
            items: List of item dicts:
                [{
                    'product': Product,
                    'variant': ProductVariant | None,
                    'quantity': int,
                    'unit_price': Decimal | None (auto-calculated if None),
                    'discount_amount': Decimal (optional),
                }]
            payments: List of payment dicts:
                [{
                    'payment_method': str (e.g., 'cash', 'card', 'mobile_banking'),
                    'amount': Decimal,
                    'is_cod': bool (True for cash),
                }]
            order_notes: Notes for the order.
            shipping_cost: Shipping charge (default 0 for POS).
            tax_amount: Tax amount.
            currency: Currency code.
            discount_amount: Order-level discount.
            created_by: User creating the sale (usually the cashier).

        Returns:
            dict: {
                'order': Order,
                'payments': list[Payment],
                'transactions': list[InventoryTransaction],
                'accounting_entries': list[AccountTransaction],
            }

        Raises:
            ValueError: If validation fails (inactive shift, stock, etc.).
        """
        # ── 1. Validate shift and register ──
        if shift.status != POSShift.Status.OPEN:
            raise ValueError(f"Shift {shift.id} is not open. Status: {shift.status}")

        try:
            register = shift.cash_register
        except CashRegister.DoesNotExist:
            raise ValueError(f"No cash register found for shift {shift.id}.")

        if register.status != CashRegister.Status.OPEN:
            raise ValueError(
                f"Cash register {register.id} is not open. Status: {register.status}"
            )

        # ── 2. Prepare items_data with pricing ──
        items_data = POSService._prepare_items_data(items)

        subtotal = sum(
            item['total_price'] for item in items_data
        )

        total_amount = max(
            subtotal + shipping_cost + tax_amount - discount_amount,
            Decimal("0")
        )

        # ── 3. Create Order ──
        from .order_service import OrderService

        order = OrderService.create_order(
            user=customer,
            source='pos',
            items_data=items_data,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=currency,
            order_notes=order_notes,
            terminal=terminal,
            shift=shift,
            cashier=cashier,
            created_by=created_by or cashier,
        )

        # ── 4. Process Payments ──
        from .payment_service import PaymentService

        payment_objs = []
        for payment_info in payments:
            payment = PaymentService.create_payment(
                order=order,
                user=customer,
                amount=payment_info['amount'],
                payment_method=payment_info['payment_method'],
                payment_channel=payment_info.get('payment_channel'),
                currency=currency,
                is_cod=payment_info.get('is_cod', False),
                status='captured',
                cash_register=register if payment_info.get('is_cod') else None,
                created_by=cashier,
            )
            payment_objs.append(payment)

        # ── 5. Confirm order (deducts inventory + records accounting) ──
        order = OrderService.confirm_order(
            order=order,
            changed_by=cashier,
        )

        # Return result
        return {
            'order': order,
            'payments': payment_objs,
        }

    # ─────────────────────────────────────────────────────────────────
    #  HOLD / RESUME SALE
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def hold_sale(
        *,
        terminal: POSTerminal,
        shift: POSShift,
        cashier,
        customer,
        items: list,
        order_notes: str = "",
    ) -> Order:
        """
        Create a held (draft/PENDING) POS order without payment or inventory deduction.

        This allows the cashier to resume the sale later.

        Args:
            terminal: POSTerminal.
            shift: POSShift.
            cashier: User operating the register.
            customer: Customer User (or walk-in).
            items: List of item dicts (same format as create_pos_sale).
            order_notes: Notes.

        Returns:
            Order instance in PENDING status.
        """
        items_data = POSService._prepare_items_data(items)
        subtotal = sum(item['total_price'] for item in items_data)

        from .order_service import OrderService

        order = OrderService.create_order(
            user=customer,
            source='pos',
            items_data=items_data,
            subtotal=subtotal,
            terminal=terminal,
            shift=shift,
            cashier=cashier,
            order_notes=order_notes or "HELD SALE",
            created_by=cashier,
        )

        return order

    @staticmethod
    @transaction.atomic
    def resume_sale(
        held_order: Order,
        payments: list,
        cashier=None,
    ) -> dict:
        """
        Resume a held POS sale — add payments, confirm, deduct inventory.

        Args:
            held_order: The PENDING order created by hold_sale().
            payments: List of payment dicts (same format as create_pos_sale).
            cashier: User processing the resumed sale.

        Returns:
            dict: {'order': Order, 'payments': list[Payment]}

        Raises:
            ValueError: If order is not in PENDING status or shift closed.
        """
        if held_order.status != Order.Status.PENDING:
            raise ValueError(
                f"Cannot resume order in status '{held_order.status}'."
            )

        shift = held_order.shift
        if not shift or shift.status != POSShift.Status.OPEN:
            raise ValueError("The shift for this held order is no longer open.")

        try:
            register = shift.cash_register
        except CashRegister.DoesNotExist:
            raise ValueError("No cash register found for the shift.")

        if register.status != CashRegister.Status.OPEN:
            raise ValueError("Cash register is not open.")

        from .payment_service import PaymentService
        from .order_service import OrderService

        payment_objs = []
        for payment_info in payments:
            payment = PaymentService.create_payment(
                order=held_order,
                user=held_order.user,
                amount=payment_info['amount'],
                payment_method=payment_info['payment_method'],
                currency=held_order.currency,
                is_cod=payment_info.get('is_cod', False),
                status='captured',
                cash_register=register if payment_info.get('is_cod') else None,
                created_by=cashier,
            )
            payment_objs.append(payment)

        order = OrderService.confirm_order(
            order=held_order,
            changed_by=cashier,
        )

        return {
            'order': order,
            'payments': payment_objs,
        }

    # ─────────────────────────────────────────────────────────────────
    #  WALK-IN CUSTOMER
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_walkin_customer(
        cashier,
        phone: str = "",
        name: str = "",
        email: str = "",
    ):
        """
        Create or find a walk-in customer for POS sales.

        Args:
            cashier: The cashier creating the customer.
            phone: Customer phone number.
            name: Customer name.
            email: Customer email.

        Returns:
            User instance (created or existing).
        """
        from django.contrib.auth import get_user_model
        from .customer_service import CustomerService

        User = get_user_model()

        # Try to find existing customer by phone
        if phone:
            existing = User.objects.filter(
                customer_profile__phone=phone
            ).first()
            if existing:
                return existing

        # Generate a unique username
        import uuid
        username = f"walkin_{uuid.uuid4().hex[:8]}"
        email = email or f"{username}@walkin.local"

        user = User.objects.create_user(
            name=name or "Walk-in Customer",
            email=email,
            password=uuid.uuid4().hex[:16],
        )
        user.role = 'customer'
        user.is_active = True
        user.save()

        CustomerService.create_customer(
            user=user,
            phone=phone,
        )

        return user

    # ─────────────────────────────────────────────────────────────────
    #  INVOICE GENERATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def generate_invoice(order: Order) -> dict:
        """
        Generate invoice data for a completed POS order.

        Args:
            order: Completed Order.

        Returns:
            dict with invoice data for frontend rendering.
        """
        items_data = []
        for item in order.items.all():
            items_data.append({
                'product_name': item.product.name if item.product else 'Deleted',
                'variant_name': item.variant.name if item.variant else None,
                'sku': item.product.sku if item.product else '',
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price),
                'discount': str(item.discount_amount or '0'),
            })

        return {
            'invoice_number': order.invoice_number or order.order_number,
            'order_number': order.order_number,
            'date': order.created_at.isoformat(),
            'terminal': order.terminal.name if order.terminal else None,
        'cashier': str(order.cashier) if order.cashier else None,
            'customer': str(order.user) if order.user else 'Walk-in',
            'items': items_data,
            'subtotal': str(order.subtotal),
            'shipping_cost': str(order.shipping_cost),
            'tax_amount': str(order.tax_amount),
            'discount_amount': str(order.discount_amount),
            'total_amount': str(order.total_amount),
            'currency': order.currency,
            'payments': [
                {
                    'method': p.payment_method,
                    'amount': str(p.amount),
                    'channel': p.payment_channel,
                }
                for p in order.payments.all()
            ],
        }

    # ─────────────────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _prepare_items_data(items: list) -> list:
        """
        Prepare items data with pricing from PricingEngine.

        For each item, calculates unit_price and creates snapshots.

        Args:
            items: Raw item list from request.

        Returns:
            Processed items_data list for OrderService.
        """
        from .pricing_service import PricingEngine
        from ..models.marketing import Campaign

        campaigns = Campaign.objects.filter(is_active=True, is_deleted=False)
        items_data = []

        for item in items:
            product = item['product']
            variant = item.get('variant')
            quantity = item['quantity']

            # Calculate price if not provided
            if 'unit_price' not in item or item['unit_price'] is None:
                campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(
                    product, campaigns_queryset=campaigns
                )
                if variant:
                    price_result = PricingEngine.calculate_variant_price(
                        variant,
                        campaign_discount_value=disc_val,
                        campaign_discount_type=disc_type,
                    )
                else:
                    price_result = PricingEngine.calculate_product_price(
                        product,
                        campaign_discount_value=disc_val,
                        campaign_discount_type=disc_type,
                    )
                unit_price = price_result['selling_price']
                item_discount = price_result['discount_amount'] * quantity
            else:
                unit_price = Decimal(str(item['unit_price']))
                item_discount = Decimal(str(item.get('discount_amount', 0)))

            total_price = unit_price * quantity

            # Create snapshots
            product_snapshot = {
                'name': product.name,
                'sku': product.sku,
                'barcode': product.barcode,
                'base_price': str(product.base_price),
            }

            variant_snapshot = None
            if variant:
                variant_snapshot = {
                    'name': variant.name,
                    'sku': variant.sku,
                }

            items_data.append({
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'discount_amount': item_discount,
                'product_snapshot': product_snapshot,
                'variant_snapshot': variant_snapshot,
            })

        return items_data