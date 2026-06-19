# =============================================================================
# COUPON SERVICE
# =============================================================================
#
# Responsibilities:
# - Validate coupons
# - Check expiry dates
# - Check usage limits
# - Check minimum order requirements
# - Calculate coupon discounts
# - Track coupon usage
#
# Dependencies:
# - Coupon / CouponGroup / CouponUsage models
# - PricingEngine (for discount calculation)
# =============================================================================

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models.marketing import Coupon, CouponUsage


class CouponService:
    """Validates, applies, and tracks coupon usage."""

    @staticmethod
    def validate_coupon(
        coupon: Coupon,
        user=None,
        order_subtotal: Decimal = None,
    ) -> dict:
        """
        Validate whether a coupon can be used.

        Args:
            coupon: Coupon to validate.
            user: User attempting to use the coupon.
            order_subtotal: Order subtotal (for minimum amount check).

        Returns:
            dict: {'valid': bool, 'reason': str | None}
        """
        if not coupon.is_active:
            return {'valid': False, 'reason': 'Coupon is not active.'}

        if coupon.is_expired:
            return {'valid': False, 'reason': 'Coupon has expired.'}

        if coupon.usage_limit and coupon.current_usage >= coupon.usage_limit:
            return {'valid': False, 'reason': 'Coupon usage limit reached.'}

        if user and coupon.max_usage_per_user:
            user_usage = CouponUsage.objects.filter(
                coupon=coupon, user=user
            ).count()
            if user_usage >= coupon.max_usage_per_user:
                return {
                    'valid': False,
                    'reason': f'Maximum usage per user ({coupon.max_usage_per_user}) reached.'
                }

        if order_subtotal is not None and coupon.min_order_amount:
            if order_subtotal < coupon.min_order_amount:
                return {
                    'valid': False,
                    'reason': (
                        f'Minimum order amount of {coupon.min_order_amount} not met. '
                        f'Current subtotal: {order_subtotal}'
                    )
                }

        if user and coupon.first_order_only:
            from ..models import Order
            if Order.objects.filter(user=user, payment_status='paid').exists():
                return {
                    'valid': False,
                    'reason': 'This coupon is for first-time orders only.'
                }

        return {'valid': True, 'reason': None}

    @staticmethod
    def apply_coupon(
        coupon: Coupon,
        order_subtotal: Decimal,
        user=None,
    ) -> dict:
        """
        Apply a coupon and calculate the discount.

        Args:
            coupon: Coupon to apply.
            order_subtotal: Order subtotal before coupon.
            user: User applying the coupon.

        Returns:
            dict: {
                'coupon_discount': Decimal,
                'final_price': Decimal,
                'valid': bool,
                'reason': str | None
            }

        Raises:
            ValueError: If coupon validation fails.
        """
        validation = CouponService.validate_coupon(
            coupon=coupon,
            user=user,
            order_subtotal=order_subtotal,
        )

        if not validation['valid']:
            return {
                'coupon_discount': Decimal("0"),
                'final_price': order_subtotal,
                'valid': False,
                'reason': validation['reason'],
            }

        from .pricing_service import PricingEngine
        result = PricingEngine.apply_coupon_discount(
            price_before_coupon=order_subtotal,
            coupon=coupon,
        )

        return {
            'coupon_discount': result['coupon_discount'],
            'final_price': result['final_price'],
            'valid': True,
            'reason': None,
        }

    @staticmethod
    @transaction.atomic
    def record_coupon_usage(
        coupon: Coupon,
        user,
        order,
        discount_applied: Decimal,
        status: str = 'used',
    ) -> CouponUsage:
        """
        Record coupon usage after successful application.

        Args:
            coupon: Coupon that was used.
            user: User who used it.
            order: Order the coupon was applied to.
            discount_applied: Actual discount amount.
            status: Usage status ('used', 'expired', etc.).

        Returns:
            CouponUsage instance.
        """
        usage = CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order,
            discount_applied=discount_applied,
            status=status,
            coupon_snapshot={
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value),
                'max_discount_amount': str(coupon.max_discount_amount) if coupon.max_discount_amount else None,
            },
        )

        coupon.current_usage += 1
        coupon.save(update_fields=['current_usage'])

        return usage

    @staticmethod
    def get_applicable_coupons(
        user=None,
        order_subtotal: Decimal = None,
        products=None,
    ) -> list:
        """
        Get all coupons that are applicable to a given context.

        Args:
            user: User to check coupon applicability for.
            order_subtotal: Order subtotal.
            products: List of products in the order.

        Returns:
            list of Coupon instances that are valid.
        """
        now = timezone.now()
        coupons = Coupon.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        )

        if user:
            coupons = coupons.exclude(
                max_usage_per_user__isnull=False,
                coupon_usage__user=user,
                coupon_usage__status='used',
            )

        valid_coupons = []
        for coupon in coupons:
            validation = CouponService.validate_coupon(
                coupon=coupon,
                user=user,
                order_subtotal=order_subtotal,
            )
            if validation['valid']:
                valid_coupons.append(coupon)

        return valid_coupons