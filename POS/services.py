# =============================================================================
#  DISCOUNT PRIORITY ENGINE
#  =============================================================================
#  Discount Application Order (highest priority first):
#
#  1. CAMPAIGN DISCOUNT  — Applies to product/variant via active Campaign
#  2. VARIANT DISCOUNT   — Applies to ProductVariant.discount_value
#  3. PRODUCT DISCOUNT   — Applies to Product.discount_value
#  4. COUPON DISCOUNT    — Applies at order level after product price calculated
#
#  RULE: Only ONE product-level discount (Campaign/Variant/Product) can win.
#  RULE: Coupon discount stacks AFTER product price is finalized.
#  RULE: Prevent duplicate stacking — highest priority discount is applied.
# =============================================================================

from decimal import Decimal
from typing import Optional
from django.utils import timezone


class PricingEngine:
    """
    Centralized pricing service that computes the final selling price
    for a product or variant, applying discount priority rules.
    """

    @staticmethod
    def calculate_product_price(
        product,
        campaign_discount_value: Optional[Decimal] = None,
        campaign_discount_type: Optional[str] = None,
        quantity: int = 1,
    ) -> dict:
        """
        Calculate final price for a non-variant product.

        Discount Priority (only one wins):
        1. Campaign Discount
        2. Product-level Discount

        Returns:
        {
            'base_price': Decimal,
            'selling_price': Decimal,
            'discount_amount': Decimal,
            'discount_source': str | None,    # 'campaign' | 'product' | None
            'campaign_id': int | None,
        }
        """
        base_price = product.base_price
        discount_amount = Decimal("0")
        discount_source = None
        campaign_id = None

        # Priority 1: Campaign Discount (highest priority)
        if campaign_discount_value is not None and campaign_discount_value > 0:
            discount_amount = PricingEngine._calculate_discount(
                base_price, campaign_discount_value, campaign_discount_type
            )
            discount_source = "campaign"
            campaign_id = getattr(product, '_applied_campaign_id', None)

        # Priority 2: Product Discount (only if no campaign discount)
        elif product.discount_type and product.discount_value > 0:
            discount_amount = PricingEngine._calculate_discount(
                base_price, product.discount_value, product.discount_type
            )
            discount_source = "product"

        selling_price = max(base_price - discount_amount, Decimal("0"))

        return {
            "base_price": base_price,
            "selling_price": selling_price,
            "discount_amount": discount_amount,
            "discount_source": discount_source,
            "campaign_id": campaign_id,
        }

    @staticmethod
    def calculate_variant_price(
        variant,
        campaign_discount_value: Optional[Decimal] = None,
        campaign_discount_type: Optional[str] = None,
        quantity: int = 1,
    ) -> dict:
        """
        Calculate final price for a variant.

        Discount Priority (only one wins):
        1. Campaign Discount
        2. Variant-level Discount
        3. Parent Product Discount (lowest priority among product-level)

        Returns:
        {
            'base_price': Decimal,
            'selling_price': Decimal,
            'discount_amount': Decimal,
            'discount_source': str | None,
            'campaign_id': int | None,
        }
        """
        base_price = variant.base_price
        discount_amount = Decimal("0")
        discount_source = None
        campaign_id = None

        # Priority 1: Campaign Discount (highest priority)
        if campaign_discount_value is not None and campaign_discount_value > 0:
            discount_amount = PricingEngine._calculate_discount(
                base_price, campaign_discount_value, campaign_discount_type
            )
            discount_source = "campaign"
            campaign_id = getattr(variant, '_applied_campaign_id', None)

        # Priority 2: Variant Discount
        elif variant.discount_type and variant.discount_value > 0:
            discount_amount = PricingEngine._calculate_discount(
                base_price, variant.discount_value, variant.discount_type
            )
            discount_source = "variant"

        # Priority 3: Parent Product Discount (lowest product-level priority)
        elif variant.product.discount_type and variant.product.discount_value > 0:
            discount_amount = PricingEngine._calculate_discount(
                base_price,
                variant.product.discount_value,
                variant.product.discount_type,
            )
            discount_source = "product"

        selling_price = max(base_price - discount_amount, Decimal("0"))

        return {
            "base_price": base_price,
            "selling_price": selling_price,
            "discount_amount": discount_amount,
            "discount_source": discount_source,
            "campaign_id": campaign_id,
        }

    @staticmethod
    def apply_coupon_discount(
        price_before_coupon: Decimal,
        coupon,
    ) -> dict:
        """
        Apply coupon discount AFTER product-level pricing is finalized.
        Coupon applies to the order total (not per-product).

        Returns:
        {
            'coupon_discount': Decimal,
            'final_price': Decimal,
        }
        """
        if not coupon or not coupon.is_active or coupon.is_expired:
            return {"coupon_discount": Decimal("0"), "final_price": price_before_coupon}

        discount = PricingEngine._calculate_discount(
            price_before_coupon, coupon.discount_value, coupon.discount_type
        )

        # Cap at max_discount_amount if set
        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)

        final_price = max(price_before_coupon - discount, Decimal("0"))

        return {
            "coupon_discount": discount,
            "final_price": final_price,
        }

    @staticmethod
    def _calculate_discount(
        price: Decimal, discount_value: Decimal, discount_type: str
    ) -> Decimal:
        """Calculate discount amount based on type."""
        if discount_type == "percentage":
            # Clamp percentage to 0-100
            valid_value = max(Decimal("0"), min(discount_value, Decimal("100")))
            return (price * valid_value / Decimal("100")).quantize(Decimal("0.01"))
        elif discount_type == "fixed":
            # Fixed discount cannot exceed price
            return min(max(discount_value, Decimal("0")), price)
        return Decimal("0")

    @staticmethod
    def find_best_campaign_for_product(product, campaigns_queryset=None):
        """
        Find the best active campaign for a product.
        Returns (campaign, discount_value, discount_type) or (None, None, None).
        """
        now = timezone.now()

        if campaigns_queryset is None:
            from .models.marketing import Campaign
            campaigns_queryset = Campaign.objects.filter(is_active=True, is_deleted=False)

        for campaign in campaigns_queryset:
            if campaign.start_date <= now <= campaign.end_date:
                # Check if product is applicable
                if product in campaign.applicable_products.all():
                    return campaign, campaign.discount_value, campaign.discount_type
                if product.category and product.category in campaign.applicable_categories.all():
                    return campaign, campaign.discount_value, campaign.discount_type
        return None, None, None