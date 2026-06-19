# =============================================================================
# LOYALTY SERVICE
# =============================================================================
#
# Responsibilities:
# - Award loyalty points for purchases
# - Redeem loyalty points for discounts
# - Calculate points earned based on order value
# - Track loyalty transaction history
# - Manage points expiry
# - Check points balance
#
# Dependencies:
# - LoyaltyPoints model
# - LoyaltyTransaction model
# - CustomerProfile model (for balance cache)
# =============================================================================

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import LoyaltyPoints, LoyaltyTransaction, CustomerProfile


class LoyaltyService:
    """Manage loyalty points — awarding, redeeming, and tracking."""

    # Default: 1 point per 100 currency units spent
    POINTS_PER_CURRENCY_UNIT = Decimal("100")
    POINTS_EXPIRY_DAYS = 365

    @staticmethod
    @transaction.atomic
    def earn_points(
        user,
        order_total: Decimal,
        reference: str = "",
        notes: str = "",
    ) -> LoyaltyTransaction:
        """
        Award loyalty points based on order total.

        Args:
            user: User earning points.
            order_total: Total amount of the order.
            reference: Reference (e.g., order number).
            notes: Additional notes.

        Returns:
            LoyaltyTransaction instance.
        """
        points = int(order_total / LoyaltyService.POINTS_PER_CURRENCY_UNIT)
        if points <= 0:
            points = 1  # Minimum 1 point per purchase

        loyalty, _ = LoyaltyPoints.objects.get_or_create(user=user)
        balance_before = loyalty.balance
        expires_at = timezone.now() + timezone.timedelta(
            days=LoyaltyService.POINTS_EXPIRY_DAYS
        )

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

        # Sync customer profile cache
        CustomerProfile.objects.filter(user=user).update(
            loyalty_points=loyalty.balance
        )

        return lt

    @staticmethod
    @transaction.atomic
    def redeem_points(
        user,
        points: int,
        reference: str = "",
        notes: str = "",
    ) -> LoyaltyTransaction:
        """
        Redeem loyalty points for a discount.

        Args:
            user: User redeeming points.
            points: Number of points to redeem.
            reference: Reference (e.g., order number).
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

        # Sync customer profile cache
        CustomerProfile.objects.filter(user=user).update(
            loyalty_points=loyalty.balance
        )

        return lt

    @staticmethod
    def get_balance(user) -> int:
        """
        Get current loyalty points balance.

        Args:
            user: User to check.

        Returns:
            int current balance.
        """
        loyalty = LoyaltyPoints.objects.filter(user=user).first()
        return loyalty.balance if loyalty else 0

    @staticmethod
    def get_points_value(points: int) -> Decimal:
        """
        Calculate the monetary value of points.
        Default: 1 point = 1 currency unit.

        Args:
            points: Number of points.

        Returns:
            Decimal monetary value.
        """
        return Decimal(str(points))

    @staticmethod
    def expire_old_points(user):
        """
        Expire points that have passed their expiry date.

        Args:
            user: User whose points to check.

        Returns:
            int number of points expired.
        """
        now = timezone.now()
        expired_transactions = LoyaltyTransaction.objects.filter(
            user=user,
            transaction_type=LoyaltyTransaction.TransactionType.EARNED,
            expires_at__lt=now,
        )

        total_expired = sum(t.points for t in expired_transactions)
        if total_expired <= 0:
            return 0

        loyalty = LoyaltyPoints.objects.get(user=user)
        balance_before = loyalty.balance

        LoyaltyTransaction.objects.create(
            user=user,
            transaction_type=LoyaltyTransaction.TransactionType.EXPIRED,
            points=total_expired,
            balance_before=balance_before,
            balance_after=balance_before - total_expired,
            notes=f"Auto-expiry of {total_expired} points",
        )

        loyalty.balance = max(balance_before - total_expired, 0)
        loyalty.save(update_fields=['balance'])

        CustomerProfile.objects.filter(user=user).update(
            loyalty_points=loyalty.balance
        )

        return total_expired