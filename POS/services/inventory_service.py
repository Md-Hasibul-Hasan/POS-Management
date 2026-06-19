# =============================================================================
# INVENTORY SERVICE
# =============================================================================
#
# Responsibilities:
# - Add stock from purchases
# - Deduct stock from sales (FIFO-aware)
# - Reserve stock for orders
# - Release reserved stock
# - Create inventory transactions (single source of truth)
# - Validate stock availability
# - Handle stock adjustments
# - Manage FIFO inventory batches
# - Handle stock audits
# - Handle supplier returns
# - Handle damaged inventory
# - Handle lost inventory
# - Maintain stock cache synchronization
#
# Dependencies:
# - InventoryTransaction model (SSoT)
# - InventoryBatch model (FIFO)
# - Product / ProductVariant models (cache fields)
# - Order model
# =============================================================================

from decimal import Decimal
from typing import Optional, List
from django.db import transaction
from django.utils import timezone
from ..models import (
    InventoryTransaction,
    InventoryBatch,
    StockReservation,
    Product,
    ProductVariant,
    Order,
    DamageReport,
    LostInventory,
    StockAdjustment,
    SupplierReturn,
    StockAudit,
)


class InventoryService:
    """Central inventory operations — all mutations go through here."""

    # ─────────────────────────────────────────────────────────────────
    #  STOCK DEDUCTION (FIFO-aware, for sales)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def deduct_stock(
        product: Product,
        quantity: int,
        transaction_type: str = InventoryTransaction.TransactionType.POS_SALE,
        variant: ProductVariant = None,
        order: Order = None,
        performed_by=None,
        notes: str = "",
        source_document: str = "",
    ) -> List[InventoryTransaction]:
        """
        Deduct stock from inventory using FIFO batch consumption.

        Creates one InventoryTransaction per batch consumed, ensuring
        the InventoryTransaction model remains the single source of truth.

        Args:
            product: Product to deduct stock from.
            quantity: Quantity to deduct (must be positive).
            transaction_type: Type of deduction (e.g., POS_SALE, ONLINE_SALE).
            variant: Specific variant (if applicable).
            order: Order this deduction relates to.
            performed_by: User performing the deduction.
            notes: Transaction notes.
            source_document: Reference document (e.g., order number).

        Returns:
            List of InventoryTransaction records created.

        Raises:
            ValueError: If insufficient stock, invalid quantity, etc.
        """
        if quantity <= 0:
            raise ValueError("Deduction quantity must be positive.")

        # Determine available stock
        available = InventoryService.get_available_stock(product, variant)
        if available < quantity:
            raise ValueError(
                f"Insufficient stock for {product.name}. "
                f"Requested: {quantity}, Available: {available}"
            )

        transactions = []
        remaining = quantity

        # Consume from FIFO batches (oldest first)
        batches = InventoryBatch.objects.filter(
            product=product,
            variant=variant,
            is_active=True,
            remaining_quantity__gt=0,
        ).order_by('purchase_date', 'id')

        for batch in batches:
            if remaining <= 0:
                break

            consume = min(batch.remaining_quantity, remaining)

            # Record current product-level stock before mutation
            current_stock = (
                variant.stock if variant else product.base_stock
            )

            # Create inventory transaction
            tx = InventoryTransaction.objects.create(
                transaction_type=transaction_type,
                product=product,
                variant=variant,
                batch=batch,
                quantity=-consume,
                previous_stock=current_stock,
                new_stock=current_stock - consume,
                source_type=InventoryTransaction.SourceType.ORDER if order else InventoryTransaction.SourceType.MANUAL,
                source_document=source_document or (
                    order.order_number if order else ""
                ),
                reference_id=order.id if order else None,
                notes=notes,
                performed_by=performed_by,
            )
            transactions.append(tx)

            # Update batch remaining quantity
            batch.remaining_quantity -= consume
            batch.save(update_fields=['remaining_quantity'])
            if batch.remaining_quantity <= 0:
                batch.is_active = False
                batch.save(update_fields=['is_active'])

            remaining -= consume

        # Update product/variant cache fields
        InventoryService._sync_stock_cache(product, variant)

        return transactions

    # ─────────────────────────────────────────────────────────────────
    #  STOCK ADDITION (for purchases, returns)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def add_stock(
        product: Product,
        quantity: int,
        cost_price: Decimal,
        transaction_type: str = InventoryTransaction.TransactionType.PURCHASE,
        variant: ProductVariant = None,
        batch: InventoryBatch = None,
        performed_by=None,
        notes: str = "",
        source_document: str = "",
        purchase_date=None,
        expiry_date=None,
        batch_number: str = "",
    ) -> InventoryTransaction:
        """
        Add stock to inventory.

        Creates a new InventoryBatch entry (FIFO layer) and records
        the inventory transaction.

        Args:
            product: Product to add stock to.
            quantity: Quantity to add (must be positive).
            cost_price: Cost price per unit for FIFO valuation.
            transaction_type: Type of addition (e.g., PURCHASE, CUSTOMER_RETURN).
            variant: Specific variant (if applicable).
            batch: Existing batch to add to (optional, creates new if None).
            performed_by: User performing the addition.
            notes: Transaction notes.
            source_document: Reference document.
            purchase_date: Date of purchase/receipt.
            expiry_date: Batch expiry date (if applicable).
            batch_number: Batch identifier.

        Returns:
            InventoryTransaction instance.
        """
        if quantity <= 0:
            raise ValueError("Addition quantity must be positive.")

        # Find or create batch
        if batch is None:
            batch = InventoryBatch.objects.create(
                product=product,
                variant=variant,
                cost_price=cost_price,
                received_quantity=quantity,
                remaining_quantity=quantity,
                purchase_date=purchase_date or timezone.now().date(),
                expiry_date=expiry_date,
                batch_number=batch_number,
                is_active=True,
            )
        else:
            batch.received_quantity += quantity
            batch.remaining_quantity += quantity
            batch.save(update_fields=['received_quantity', 'remaining_quantity'])
            if not batch.is_active:
                batch.is_active = True
                batch.save(update_fields=['is_active'])

        # Record current stock
        current_stock = variant.stock if variant else product.base_stock

        tx = InventoryTransaction.objects.create(
            transaction_type=transaction_type,
            product=product,
            variant=variant,
            batch=batch,
            quantity=+quantity,
            previous_stock=current_stock,
            new_stock=current_stock + quantity,
            source_type=InventoryTransaction.SourceType.MANUAL,
            source_document=source_document,
            notes=notes,
            performed_by=performed_by,
        )

        # Update product/variant cache fields
        InventoryService._sync_stock_cache(product, variant)

        return tx

    # ─────────────────────────────────────────────────────────────────
    #  STOCK RESERVATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def reserve_stock(
        product: Product,
        quantity: int,
        order: Order,
        user,
        variant: ProductVariant = None,
        cart_item=None,
        reservation_source: str = StockReservation.Source.CART,
        checkout_token: str = None,
        performed_by=None,
    ) -> StockReservation:
        """
        Reserve stock for a pending order/cart.

        This does NOT deduct physical stock. It creates a reservation
        that prevents over-selling until the order is confirmed.

        Args:
            product: Product to reserve.
            quantity: Quantity to reserve.
            order: Order this reservation is for.
            user: User/customer making the reservation.
            variant: Specific variant (if applicable).
            cart_item: CartItem this reservation relates to.
            reservation_source: Source of reservation (cart, checkout, admin).
            checkout_token: Token for checkout session.
            performed_by: User who initiated the reservation.

        Returns:
            StockReservation instance.

        Raises:
            ValueError: If insufficient available stock.
        """
        available = InventoryService.get_available_stock(product, variant)
        if available < quantity:
            raise ValueError(
                f"Insufficient available stock for {product.name}. "
                f"Requested: {quantity}, Available: {available}"
            )

        # Calculate expiry (default 30 minutes for cart, 24h for checkout)
        if reservation_source == StockReservation.Source.CART:
            expires_at = timezone.now() + timezone.timedelta(minutes=30)
        else:
            expires_at = timezone.now() + timezone.timedelta(hours=24)

        reservation = StockReservation.objects.create(
            product=product,
            variant=variant,
            order=order,
            cart_item=cart_item,
            user=user,
            quantity=quantity,
            status=StockReservation.Status.ACTIVE,
            reservation_source=reservation_source,
            checkout_token=checkout_token,
            expires_at=expires_at,
        )

        # Update cache: increase reserved count
        if variant:
            variant.reserved_stock += quantity
            variant.save(update_fields=['reserved_stock'])
        else:
            product.reserved_stock += quantity
            product.save(update_fields=['reserved_stock'])

        # Create inventory transaction for reservation
        current_stock = variant.stock if variant else product.base_stock
        InventoryTransaction.objects.create(
            transaction_type=InventoryTransaction.TransactionType.RESERVATION,
            product=product,
            variant=variant,
            quantity=-quantity,
            previous_stock=current_stock,
            new_stock=current_stock,
            source_type=InventoryTransaction.SourceType.ORDER,
            source_document=order.order_number,
            reference_id=order.id,
            notes=f"Reservation for order {order.order_number}",
            performed_by=performed_by,
        )

        return reservation

    @staticmethod
    @transaction.atomic
    def release_stock(
        reservation: StockReservation,
        performed_by=None,
    ) -> StockReservation:
        """
        Release a previously held stock reservation.

        This is called when a cart expires, order is cancelled,
        or reservation is manually released.

        Args:
            reservation: StockReservation to release.
            performed_by: User who released the reservation.

        Returns:
            Updated StockReservation instance.
        """
        if reservation.status != StockReservation.Status.ACTIVE:
            raise ValueError(
                f"Cannot release reservation in status '{reservation.status}'."
            )

        reservation.status = StockReservation.Status.RELEASED
        reservation.released_at = timezone.now()
        reservation.save()

        # Update cache: decrease reserved count
        if reservation.variant:
            reservation.variant.reserved_stock = max(
                reservation.variant.reserved_stock - reservation.quantity, 0
            )
            reservation.variant.save(update_fields=['reserved_stock'])
        else:
            reservation.product.reserved_stock = max(
                reservation.product.reserved_stock - reservation.quantity, 0
            )
            reservation.product.save(update_fields=['reserved_stock'])

        # Create release inventory transaction
        current_stock = (
            reservation.variant.stock if reservation.variant
            else reservation.product.base_stock
        )
        InventoryTransaction.objects.create(
            transaction_type=InventoryTransaction.TransactionType.RESERVATION_RELEASE,
            product=reservation.product,
            variant=reservation.variant,
            quantity=+reservation.quantity,
            previous_stock=current_stock,
            new_stock=current_stock,
            source_type=InventoryTransaction.SourceType.SYSTEM,
            source_document=reservation.order.order_number,
            reference_id=reservation.id,
            notes=f"Released reservation for order {reservation.order.order_number}",
            performed_by=performed_by,
        )

        return reservation

    # ─────────────────────────────────────────────────────────────────
    #  STOCK ADJUSTMENT
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def adjust_stock(
        product: Product,
        quantity: int,
        reason: str,
        variant: ProductVariant = None,
        notes: str = "",
        performed_by=None,
    ) -> InventoryTransaction:
        """
        Perform a manual stock adjustment.

        Positive quantity = stock increase.
        Negative quantity = stock decrease.

        Args:
            product: Product to adjust.
            quantity: Adjustment quantity (+ or -).
            reason: Why the adjustment is being made.
            variant: Specific variant (if applicable).
            notes: Additional notes.
            performed_by: User performing the adjustment.

        Returns:
            InventoryTransaction instance.

        Raises:
            ValueError: If adjustment would make stock negative.
        """
        if quantity == 0:
            raise ValueError("Adjustment quantity cannot be zero.")

        current_stock = variant.stock if variant else product.base_stock
        new_stock = current_stock + quantity

        if new_stock < 0:
            raise ValueError(
                f"Cannot adjust stock below zero. "
                f"Current: {current_stock}, Adjustment: {quantity}"
            )

        tx = InventoryTransaction.objects.create(
            transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT,
            product=product,
            variant=variant,
            quantity=quantity,
            previous_stock=current_stock,
            new_stock=new_stock,
            source_type=InventoryTransaction.SourceType.MANUAL,
            notes=notes or reason,
            performed_by=performed_by,
        )

        StockAdjustment.objects.create(
            product=product,
            variant=variant,
            quantity=quantity,
            previous_stock=current_stock,
            new_stock=new_stock,
            reason=reason,
            notes=notes,
            adjusted_by=performed_by,
        )

        batch = InventoryBatch.objects.filter(
            product=product,
            is_active=True
        ).order_by('-id').first()

        if batch:
            batch.received_quantity += quantity
            batch.remaining_quantity += quantity
            batch.save()

        InventoryService._sync_stock_cache(product, variant)

        return tx

    # ─────────────────────────────────────────────────────────────────
    #  STOCK AVAILABILITY
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_available_stock(product: Product, variant: ProductVariant = None) -> int:
        """
        Get currently available stock (physical - reserved).

        Args:
            product: Product to check.
            variant: Specific variant (if applicable).

        Returns:
            int Available quantity.
        """
        if variant:
            return max(variant.stock - variant.reserved_stock, 0)
        if product.has_variants:
            variants = product.variants.filter(is_deleted=False)
            return sum(
                max(v.stock - v.reserved_stock, 0) for v in variants
            )
        return max(product.base_stock - product.reserved_stock, 0)

    # ─────────────────────────────────────────────────────────────────
    #  CACHE SYNCHRONIZATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _sync_stock_cache(
        product: Product,
        variant: ProductVariant = None,
    ):
        """
        Synchronize the stock cache fields on Product/ProductVariant.

        These cache fields are NOT the source of truth — they are
        derived from InventoryBatch.remaining_quantity for performance.

        Called automatically after any stock mutation.
        """
        from django.db.models import Sum

        if variant:
            total = InventoryBatch.objects.filter(
                product=product,
                variant=variant,
                is_active=True,
            ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
            variant.stock = total
            variant.save(update_fields=['stock'])

        # Always sync product-level (aggregates all variants + base)
        if product.has_variants:
            # Sum all variant stocks + any product-level batches
            total_product = InventoryBatch.objects.filter(
                product=product,
                variant__isnull=True,
                is_active=True,
            ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
            total_variants = InventoryBatch.objects.filter(
                product=product,
                variant__isnull=False,
                is_active=True,
            ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
            product.base_stock = total_product + total_variants
        else:
            total = InventoryBatch.objects.filter(
                product=product,
                is_active=True,
            ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
            product.base_stock = total

        product.save(update_fields=['base_stock'])

    # ─────────────────────────────────────────────────────────────────
    #  DAMAGE / LOST REPORTING
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def report_damage(
        product: Product,
        quantity: int,
        reason: str,
        variant: ProductVariant = None,
        notes: str = "",
        reported_by=None,
    ) -> InventoryTransaction:
        """
        Report damaged inventory and deduct from stock.

        Args:
            product: Damaged product.
            quantity: Quantity damaged.
            reason: Cause of damage.
            variant: Specific variant (if applicable).
            notes: Additional notes.
            reported_by: User reporting the damage.

        Returns:
            InventoryTransaction instance.
        """
        damage = DamageReport.objects.create(
            product=product,
            variant=variant,
            quantity=quantity,
            reason=reason,
            notes=notes,
            reported_by=reported_by,
            damage_date=timezone.now(),
        )

        return InventoryService.deduct_stock(
            product=product,
            quantity=quantity,
            transaction_type=InventoryTransaction.TransactionType.DAMAGE,
            variant=variant,
            performed_by=reported_by,
            notes=f"Damage: {reason}. Report #{damage.id}",
        )

    # ─────────────────────────────────────────────────────────────────
    #  STOCK AUDIT
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def perform_audit(
        product: Product,
        physical_stock: int,
        variant: ProductVariant = None,
        notes: str = "",
        audited_by=None,
    ) -> StockAudit:
        """
        Perform a stock audit: compare system vs physical count.

        If there's a variance, creates an adjustment transaction
        to sync system stock with physical count.

        Args:
            product: Product being audited.
            physical_stock: Actual physical count.
            variant: Specific variant (if applicable).
            notes: Audit notes.
            audited_by: User performing the audit.

        Returns:
            StockAudit instance.
        """
        system_stock = variant.stock if variant else product.base_stock
        variance = physical_stock - system_stock

        audit = StockAudit.objects.create(
            product=product,
            variant=variant,
            system_stock=system_stock,
            physical_stock=physical_stock,
            variance=variance,
            status=StockAudit.Status.COMPLETED,
            notes=notes,
            audited_by=audited_by,
            audit_date=timezone.now(),
        )

        # Auto-adjust if variance detected
        if variance != 0:
            InventoryService.adjust_stock(
                product=product,
                quantity=variance,
                reason=f"Stock audit #{audit.id} correction",
                variant=variant,
                notes=f"Audit variance: {variance:+d}. System: {system_stock}, Physical: {physical_stock}",
                performed_by=audited_by,
            )

        return audit