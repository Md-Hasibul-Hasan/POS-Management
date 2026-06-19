# =============================================================================
# CUSTOMER SERVICE
# =============================================================================
#
# Responsibilities:
# - Create customer profiles
# - Update customer statistics
# - Manage customer wallets
# - Manage customer ledgers
# - Manage customer addresses
# - Handle customer activities
# - Manage customer groups
# - Manage loyalty profiles
# - Manage wishlists
# - Manage customer lifecycle statistics
#
# Dependencies:
# - CustomerProfile model
# - CustomerLedger model
# - WalletTransaction model
# - LoyaltyPoints / LoyaltyTransaction models
# - Address model
# =============================================================================

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import (
    CustomerProfile,
    CustomerLedger,
    CustomerGroup,
    WalletTransaction,
    LoyaltyPoints,
    LoyaltyTransaction,
    Address,
    Wishlist,
)


class CustomerService:
    """Manages customer data — profiles, wallets, ledgers, addresses."""

    # ─────────────────────────────────────────────────────────────────
    #  CUSTOMER PROFILE
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_customer(
        user,
        phone: str = "",
        group=None,
        referral_code: str = "",
        referred_by=None,
        notes: str = "",
    ) -> CustomerProfile:
        """
        Create a customer profile for a user.

        Args:
            user: User instance (from auth system).
            phone: Customer phone number.
            group: CustomerGroup this customer belongs to.
            referral_code: Unique referral code for this customer.
            referred_by: CustomerProfile who referred this customer.
            notes: Additional notes.

        Returns:
            CustomerProfile instance.
        """
        # Auto-generate customer_id if not set
        customer_id = f"CUST-{user.id:06d}"

        profile, created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                'customer_id': customer_id,
                'phone': phone,
                'group': group,
                'referral_code': referral_code or customer_id,
                'referred_by': referred_by,
                'notes': notes,
            }
        )

        if not created:
            # Update existing profile with provided data
            if phone:
                profile.phone = phone
            if group:
                profile.group = group
            if notes:
                profile.notes = notes
            profile.save()

        # Initialize loyalty points
        LoyaltyPoints.objects.get_or_create(user=user)

        return profile

    @staticmethod
    @transaction.atomic
    def update_customer_stats(customer_profile: CustomerProfile):
        """
        Recalculate and update customer statistics from order data.

        Args:
            customer_profile: CustomerProfile to update.

        Returns:
            Updated CustomerProfile instance.
        """
        from django.db.models import Sum, Count
        from ..models import Order

        user = customer_profile.user
        stats = Order.objects.filter(
            user=user,
            payment_status=Order.PaymentStatus.PAID,
        ).aggregate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
        )

        customer_profile.total_orders = stats['total_orders'] or 0
        customer_profile.total_spent = stats['total_spent'] or Decimal("0")
        customer_profile.save(update_fields=['total_orders', 'total_spent'])

        return customer_profile

    # ─────────────────────────────────────────────────────────────────
    #  CUSTOMER LEDGER
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_customer_ledger(
        customer,
        transaction_type: str,
        amount: Decimal,
        reference: str = "",
        notes: str = "",
        created_by=None,
    ) -> CustomerLedger:
        """
        Record a customer ledger entry and update running balance.

        Args:
            customer: User (customer) for the ledger entry.
            transaction_type: One of 'sale', 'payment', 'return', 'refund', 'adjustment'.
            amount: Transaction amount.
            reference: Reference document (e.g., order number).
            notes: Additional notes.
            created_by: User who created this entry.

        Returns:
            CustomerLedger instance.
        """
        # Calculate running balance
        last_entry = CustomerLedger.objects.filter(
            customer=customer,
        ).order_by('-created_at').first()

        balance_before = last_entry.balance_after if last_entry else Decimal("0")

        # Determine balance impact
        # Sales and refunds increase balance (customer owes more)
        # Payments decrease balance (customer paid)
        if transaction_type in ('sale', 'refund', 'return'):
            balance_after = balance_before + amount
        elif transaction_type in ('payment', 'adjustment'):
            balance_after = balance_before - amount
        else:
            balance_after = balance_before

        return CustomerLedger.objects.create(
            customer=customer,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            reference=reference,
            notes=notes,
            created_by=created_by or customer,
        )

    # ─────────────────────────────────────────────────────────────────
    #  WALLET
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_wallet(
        user,
        amount: Decimal,
        transaction_type: str,
        reference: str = "",
        notes: str = "",
        status: str = WalletTransaction.Status.COMPLETED,
    ) -> WalletTransaction:
        """
        Update customer wallet balance.

        Args:
            user: User whose wallet to update.
            amount: Amount to credit or debit.
            transaction_type: 'credit' or 'debit'.
            reference: Reference document.
            notes: Additional notes.
            status: Transaction status (default COMPLETED).

        Returns:
            WalletTransaction instance.

        Raises:
            ValueError: If debit exceeds wallet balance.
        """
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        balance_before = profile.wallet_balance

        if transaction_type == 'debit' and amount > balance_before:
            raise ValueError(
                f"Insufficient wallet balance. "
                f"Balance: {balance_before}, Requested debit: {amount}"
            )

        if transaction_type == 'credit':
            balance_after = balance_before + amount
        else:
            balance_after = balance_before - amount

        wt = WalletTransaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            status=status,
            reference=reference,
            notes=notes,
        )

        # Update profile wallet balance
        profile.wallet_balance = balance_after
        profile.save(update_fields=['wallet_balance'])

        return wt

    # ─────────────────────────────────────────────────────────────────
    #  LOYALTY POINTS
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def award_loyalty_points(
        user,
        points: int,
        reference: str = "",
        notes: str = "",
    ) -> LoyaltyTransaction:
        """
        Award loyalty points to a customer.

        Args:
            user: User to award points to.
            points: Number of points to award.
            reference: Reference document.
            notes: Additional notes.

        Returns:
            LoyaltyTransaction instance.
        """
        loyalty, _ = LoyaltyPoints.objects.get_or_create(user=user)
        balance_before = loyalty.balance

        # Points expire in 1 year
        expires_at = timezone.now() + timezone.timedelta(days=365)

        lt = LoyaltyTransaction.objects.create(
            user=user,
            transaction_type=LoyaltyTransaction.TransactionType.EARNED,
            points=points,
            balance_before=balance_before,
            balance_after=balance_before + points,
            reference=reference,
            expires_at=expires_at,
            notes=notes,
        )

        loyalty.balance += points
        loyalty.lifetime_earned += points
        loyalty.save(update_fields=['balance', 'lifetime_earned'])

        return lt

    @staticmethod
    @transaction.atomic
    def redeem_loyalty_points(
        user,
        points: int,
        reference: str = "",
        notes: str = "",
    ) -> LoyaltyTransaction:
        """
        Redeem loyalty points.

        Args:
            user: User redeeming points.
            points: Number of points to redeem.
            reference: Reference document.
            notes: Additional notes.

        Returns:
            LoyaltyTransaction instance.

        Raises:
            ValueError: If insufficient points.
        """
        loyalty, _ = LoyaltyPoints.objects.get_or_create(user=user)
        if loyalty.balance < points:
            raise ValueError(
                f"Insufficient loyalty points. "
                f"Balance: {loyalty.balance}, Requested: {points}"
            )

        balance_before = loyalty.balance

        lt = LoyaltyTransaction.objects.create(
            user=user,
            transaction_type=LoyaltyTransaction.TransactionType.REDEEMED,
            points=points,
            balance_before=balance_before,
            balance_after=balance_before - points,
            reference=reference,
            notes=notes,
        )

        loyalty.balance -= points
        loyalty.lifetime_redeemed += points
        loyalty.save(update_fields=['balance', 'lifetime_redeemed'])

        return lt

    # ─────────────────────────────────────────────────────────────────
    #  ADDRESS
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def set_default_address(address: Address):
        """
        Set an address as the default for its user.

        All other addresses for this user are unset as default.

        Args:
            address: Address to set as default.
        """
        Address.objects.filter(
            user=address.user,
            is_default=True,
        ).exclude(id=address.id).update(is_default=False)

        address.is_default = True
        address.save(update_fields=['is_default'])

        # Update customer profile default address
        profile = CustomerProfile.objects.filter(user=address.user).first()
        if profile:
            profile.default_address = address
            profile.save(update_fields=['default_address'])