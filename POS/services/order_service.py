# =============================================================================
# ORDER SERVICE
# =============================================================================
#
# Responsibilities:
# - Create orders (POS + Online)
# - Create order items
# - Confirm orders (with inventory deduction)
# - Cancel orders (with inventory release)
# - Complete orders
# - Update order status
# - Create order snapshots
# - Apply coupons
# - Calculate totals
# - Create status logs
# - Trigger fulfillment workflow
# - Trigger shipment workflow
# - **Recalculate cart totals**
# - **Calculate cart item prices**
# - **Validate coupons for order**
#
# Dependencies:
# - Order model
# - OrderItem model
# - Cart / CartItem models
# - Coupon / CouponUsage models
# - PricingEngine service
# - InventoryService (for stock deduction/release)
# - AccountingService (for financial entries)
# =============================================================================

from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from ..models import (
    Order,
    OrderItem,
    OrderStatusLog,
    OrderCoupon,
    Cart,
    CartItem,
    Product,
    ProductVariant,
)


class OrderService:
    """Manages order lifecycle — create, confirm, cancel, complete."""

    # ─────────────────────────────────────────────────────────────────
    #  ORDER CREATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_order(
        user,
        source: str = 'pos',
        items_data: list = None,
        subtotal: Decimal = None,
        shipping_cost: Decimal = Decimal("0"),
        tax_amount: Decimal = Decimal("0"),
        discount_amount: Decimal = Decimal("0"),
        total_amount: Decimal = None,
        currency: str = "BDT",
        order_notes: str = "",
        terminal=None,
        shift=None,
        cashier=None,
        shipping_address=None,
        billing_address=None,
        created_by=None,
        **extra_fields,
    ) -> Order:
        """
        Create an order with items from provided data.

        This is the single entry point for ALL order creation
        (both POS and Online).

        For POS sales, use POSService.create_pos_sale() which calls this
        and then triggers payment, inventory, and accounting.

        Args:
            user: Customer placing the order.
            source: Order source ('pos', 'online', 'web', 'mobile', 'admin', 'api').
            items_data: List of dicts with product, variant, quantity, etc.
            subtotal: Order subtotal (calculated from items if not provided).
            shipping_cost: Shipping charge.
            tax_amount: Tax amount.
            discount_amount: Discount amount.
            total_amount: Order total (calculated if not provided).
            currency: Currency code.
            order_notes: Order notes.
            terminal: POSTerminal (for POS orders).
            shift: POSShift (for POS orders).
            cashier: User (cashier for POS orders).
            shipping_address: Address for shipping.
            billing_address: Address for billing.
            created_by: User creating the order.
            **extra_fields: Additional Order model fields.

        Returns:
            Order instance.

        Raises:
            ValueError: If required data is missing or invalid.
        """
        # Generate order number
        order_number = OrderService._generate_order_number(source)
        invoice_number = OrderService._generate_invoice_number()

        # If items_data provided, calculate financials
        if items_data:
            calculated = OrderService._calculate_order_totals(items_data)
            subtotal = calculated['subtotal']
            discount_amount = calculated['discount_amount']
            if total_amount is None:
                total_amount = max(
                    subtotal + shipping_cost + tax_amount - discount_amount,
                    Decimal("0")
                )

        if total_amount is None:
            total_amount = max(
                (subtotal or Decimal("0"))
                + shipping_cost
                + tax_amount
                - discount_amount,
                Decimal("0")
            )

        order = Order.objects.create(
            order_number=order_number,
            invoice_number=invoice_number,
            user=user,
            source=source,
            status=Order.Status.PENDING,
            payment_status=Order.PaymentStatus.UNPAID,
            fulfillment_status=Order.FulfillmentStatus.PENDING,
            subtotal=subtotal or Decimal("0"),
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=currency,
            order_notes=order_notes,
            terminal=terminal,
            shift=shift,
            cashier=cashier or created_by,
            shipping_address=shipping_address,
            billing_address=billing_address or shipping_address,
            created_by=created_by,
            **extra_fields,
        )

        # Create order items if provided
        if items_data:
            OrderService._create_order_items(order, items_data)

        # Create status log
        OrderStatusLog.objects.create(
            order=order,
            new_status=Order.Status.PENDING,
            changed_by=created_by or user,
            note=f"Order created via {source}",
        )

        return order

    @staticmethod
    def _generate_order_number(source: str) -> str:
        """Generate a unique order number with source prefix."""
        import uuid
        prefix = source.upper()[:3]
        unique_id = uuid.uuid4().hex[:12].upper()
        return f"{prefix}-{unique_id}"

    @staticmethod
    def _generate_invoice_number() -> str:
        """Generate a unique invoice number."""
        import uuid
        return f"INV-{uuid.uuid4().hex[:10].upper()}"

    @staticmethod
    def _create_order_items(order: Order, items_data: list):
        """
        Create OrderItem records for an order.

        items_data format:
        [
            {
                'product': Product instance,
                'variant': ProductVariant instance (optional),
                'quantity': int,
                'unit_price': Decimal,
                'total_price': Decimal,
                'cost_price': Decimal (optional),
                'tax_amount': Decimal (optional),
                'discount_amount': Decimal (optional),
                'product_snapshot': dict (optional),
                'variant_snapshot': dict (optional),
            },
            ...
        ]
        """
        for item_data in items_data:
            product = item_data['product']
            variant = item_data.get('variant')
            quantity = item_data['quantity']
            unit_price = item_data.get('unit_price', Decimal("0"))
            total_price = item_data.get('total_price', unit_price * quantity)

            # Create snapshots
            product_snapshot = item_data.get('product_snapshot') or {
                'name': product.name,
                'sku': product.sku,
                'barcode': product.barcode,
            }

            variant_snapshot = item_data.get('variant_snapshot')
            if variant and not variant_snapshot:
                variant_snapshot = {
                    'name': variant.name,
                    'sku': variant.sku,
                }

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                cost_price=item_data.get('cost_price'),
                tax_amount=item_data.get('tax_amount', Decimal("0")),
                discount_amount=item_data.get('discount_amount', Decimal("0")),
                product_snapshot=product_snapshot,
                variant_snapshot=variant_snapshot or {},
            )

    # ─────────────────────────────────────────────────────────────────
    #  ORDER CONFIRMATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def confirm_order(
        order: Order,
        changed_by=None,
    ) -> Order:
        """
        Confirm an order and deduct inventory.

        This is called after payment is completed.

        Args:
            order: Order to confirm.
            changed_by: User confirming the order.

        Returns:
            Updated Order instance.
        """
        if order.status != Order.Status.PENDING:
            raise ValueError(
                f"Cannot confirm order in status '{order.status}'."
            )

        # Verify at least one captured payment exists
        if not order.payments.filter(status='captured').exists():
            raise ValueError(
                f"Cannot confirm order {order.order_number} without a captured payment."
            )

        order.status = Order.Status.CONFIRMED
        order.confirmed_at = timezone.now()
        order.payment_status = Order.PaymentStatus.PAID
        order.save()

        # Create status log
        OrderStatusLog.objects.create(
            order=order,
            previous_status=Order.Status.PENDING,
            new_status=Order.Status.CONFIRMED,
            changed_by=changed_by,
            note="Order confirmed (payment received)",
        )

        # Deduct inventory for each item
        from .inventory_service import InventoryService
        from ..models import InventoryTransaction

        for item in order.items.all():
            InventoryService.deduct_stock(
                product=item.product,
                quantity=item.quantity,
                transaction_type=(
                    InventoryTransaction.TransactionType.POS_SALE
                    if order.source == 'pos'
                    else InventoryTransaction.TransactionType.ONLINE_SALE
                ),
                variant=item.variant,
                order=order,
                performed_by=changed_by,
                source_document=order.order_number,
                notes=f"Sale {order.source.upper()} - {order.order_number}",
            )

        # Record accounting entries
        from .accounting_service import AccountingService
        AccountingService.record_sale(order=order, created_by=changed_by)

        # Update customer stats
        if order.user and order.user.is_authenticated:
            from .customer_service import CustomerService
            profile = getattr(order.user, 'customer_profile', None)
            if profile:
                CustomerService.update_customer_stats(profile)

            # Record customer ledger
            CustomerService.update_customer_ledger(
                customer=order.user,
                transaction_type='sale',
                amount=order.total_amount,
                reference=order.order_number,
                notes=f"{order.source.upper()} sale confirmed",
                created_by=changed_by,
            )

            # Award loyalty points
            from .loyalty_service import LoyaltyService
            LoyaltyService.earn_points(
                user=order.user,
                order_total=order.total_amount,
                reference=order.order_number,
                notes=f"Points from {order.source.upper()} order",
            )

        return order

    # ─────────────────────────────────────────────────────────────────
    #  ORDER CANCELLATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def cancel_order(
        order: Order,
        reason: str = "",
        changed_by=None,
    ) -> Order:
        """
        Cancel an order and release any reserved stock.

        Args:
            order: Order to cancel.
            reason: Reason for cancellation.
            changed_by: User cancelling the order.

        Returns:
            Updated Order instance.
        """
        if order.status in (Order.Status.CANCELLED, Order.Status.DELIVERED):
            raise ValueError(
                f"Cannot cancel order in status '{order.status}'."
            )

        order.status = Order.Status.CANCELLED
        order.cancelled_at = timezone.now()
        order.save()

        # Create status log
        OrderStatusLog.objects.create(
            order=order,
            previous_status=order.status,
            new_status=Order.Status.CANCELLED,
            changed_by=changed_by,
            note=reason or "Order cancelled",
        )

        # Release any active stock reservations
        from .inventory_service import InventoryService

        active_reservations = order.reservations.filter(
            status='active'
        )
        for reservation in active_reservations:
            InventoryService.release_stock(
                reservation=reservation,
                performed_by=changed_by,
            )

        return order

    # ─────────────────────────────────────────────────────────────────
    #  ORDER COMPLETION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def complete_order(
        order: Order,
        changed_by=None,
    ) -> Order:
        """
        Mark an order as completed/delivered.

        Args:
            order: Order to complete.
            changed_by: User marking completion.

        Returns:
            Updated Order instance.
        """
        order.status = Order.Status.DELIVERED
        order.fulfillment_status = Order.FulfillmentStatus.DELIVERED
        order.delivered_at = timezone.now()
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            previous_status=order.status,
            new_status=Order.Status.DELIVERED,
            changed_by=changed_by,
            note="Order completed/delivered",
        )

        return order

    # ─────────────────────────────────────────────────────────────────
    #  STATUS UPDATE
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_order_status(
        order: Order,
        new_status: str,
        note: str = "",
        changed_by=None,
    ) -> Order:
        """
        Update order status with audit log entry.

        Args:
            order: Order to update.
            new_status: Target status.
            note: Optional note for the status change.
            changed_by: User making the change.

        Returns:
            Updated Order instance.
        """
        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status'])

        OrderStatusLog.objects.create(
            order=order,
            previous_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            note=note,
        )

        return order

    # ─────────────────────────────────────────────────────────────────
    #  CART OPERATIONS (moved from CartItemSerializer)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def calculate_cart_item_price(cart_item: CartItem) -> dict:
        """
        Calculate the final unit price for a cart item.

        Delegates to PricingEngine for discount priority logic.
        This replaces the business logic that was in CartItemSerializer.

        Args:
            cart_item: CartItem to calculate price for.

        Returns:
            dict with 'unit_price', 'total_price', 'discount_amount',
                  'discount_source', 'campaign_id'.
        """
        from .pricing_service import PricingEngine
        from ..models.marketing import Campaign

        now = timezone.now()
        campaigns = Campaign.objects.filter(is_active=True, is_deleted=False)

        if cart_item.variant:
            campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(
                cart_item.product, campaigns_queryset=campaigns
            )
            result = PricingEngine.calculate_variant_price(
                cart_item.variant,
                campaign_discount_value=disc_val,
                campaign_discount_type=disc_type,
            )
        else:
            campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(
                cart_item.product, campaigns_queryset=campaigns
            )
            result = PricingEngine.calculate_product_price(
                cart_item.product,
                campaign_discount_value=disc_val,
                campaign_discount_type=disc_type,
            )

        return {
            'unit_price': result['selling_price'],
            'total_price': result['selling_price'] * cart_item.quantity,
            'discount_amount': result['discount_amount'] * cart_item.quantity,
            'discount_source': result['discount_source'],
            'campaign_id': result['campaign_id'],
        }

    @staticmethod
    def recalculate_cart_totals(cart: Cart) -> Cart:
        """
        Recalculate all cart totals from its items.

        This replaces the business logic that was in CartItemSerializer.
        Called after any item add/update/delete.

        Args:
            cart: Cart to recalculate.

        Returns:
            Updated Cart instance.
        """
        subtotal = Decimal("0")
        discount_amount = Decimal("0")

        for item in cart.items.all():
            price_info = OrderService.calculate_cart_item_price(item)
            subtotal += price_info['total_price']
            discount_amount += price_info['discount_amount']

        cart.subtotal = subtotal
        cart.discount_amount = discount_amount
        cart.total_amount = max(subtotal - discount_amount, Decimal("0"))
        cart.save(update_fields=['subtotal', 'discount_amount', 'total_amount'])

        return cart

    @staticmethod
    def validate_coupons_for_order(subtotal: Decimal, coupon_ids: list) -> Decimal:
        """
        Validate and calculate coupon discounts for an order.

        This replaces the business logic that was in OrderSerializer.
        Returns the total coupon discount applicable.

        Args:
            subtotal: Order subtotal before coupon discount.
            coupon_ids: List of Coupon primary keys.

        Returns:
            Decimal total coupon discount.

        Raises:
            ValueError: If total discount exceeds subtotal.
        """
        if not coupon_ids:
            return Decimal("0")

        from .pricing_service import PricingEngine
        from ..models.marketing import Coupon

        coupons = Coupon.objects.filter(id__in=coupon_ids, is_active=True)
        total_discount = Decimal("0")

        for coupon in coupons:
            result = PricingEngine.apply_coupon_discount(
                price_before_coupon=subtotal,
                coupon=coupon,
            )
            total_discount += result['coupon_discount']

        if total_discount > subtotal:
            raise ValueError(
                f"Total coupon discount ({total_discount}) "
                f"cannot exceed subtotal ({subtotal})."
            )

        return total_discount

    @staticmethod
    def _calculate_order_totals(items_data: list) -> dict:
        """
        Calculate aggregate financials from order items data.

        Args:
            items_data: List of item dicts with quantity, unit_price, etc.

        Returns:
            dict with 'subtotal', 'discount_amount'.
        """
        subtotal = Decimal("0")
        discount_amount = Decimal("0")

        for item in items_data:
            quantity = item.get('quantity', 1)
            unit_price = item.get('unit_price', Decimal("0"))
            item_discount = item.get('discount_amount', Decimal("0"))

            subtotal += unit_price * quantity
            discount_amount += item_discount

        return {
            'subtotal': subtotal,
            'discount_amount': discount_amount,
        }