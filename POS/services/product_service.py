# =============================================================================
# PRODUCT SERVICE
# =============================================================================
#
# Responsibilities:
# - Calculate final product price with campaign discounts
# - Calculate final variant price with campaign discounts
# - Provide price data for serializers (presentation layer)
# - Handle product-related queries that involve business logic
#
# Dependencies:
# - PricingEngine service
# - Product / ProductVariant models
# - Campaign model
# =============================================================================

from ..services.pricing_service import PricingEngine
from ..models.marketing import Campaign


class ProductService:
    """
    Product-related business logic.
    Used by serializers for read-only price calculations.
    """

    @staticmethod
    def get_product_final_price(product):
        """
        Calculate the final price for a non-variant product.

        Args:
            product: Product instance.

        Returns:
            dict with base_price, selling_price, discount_amount,
                 discount_source, campaign_id (all strings for serialization).
        """
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(product)
        result = PricingEngine.calculate_product_price(
            product,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        return {
            "base_price": str(result["base_price"]),
            "selling_price": str(result["selling_price"]),
            "discount_amount": str(result["discount_amount"]),
            "discount_source": result["discount_source"],
            "campaign_id": campaign.id if campaign else None,
        }

    @staticmethod
    def get_variant_final_price(variant):
        """
        Calculate the final price for a variant.

        Args:
            variant: ProductVariant instance.

        Returns:
            dict with base_price, selling_price, discount_amount,
                 discount_source, campaign_id (all strings for serialization).
        """
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(variant.product)
        result = PricingEngine.calculate_variant_price(
            variant,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        return {
            "base_price": str(result["base_price"]),
            "selling_price": str(result["selling_price"]),
            "discount_amount": str(result["discount_amount"]),
            "discount_source": result["discount_source"],
            "campaign_id": campaign.id if campaign else None,
        }

    @staticmethod
    def get_product_primary_image(product):
        """
        Get the primary image URL for a product.

        Args:
            product: Product instance.

        Returns:
            str URL or None.
        """
        primary = product.images.filter(is_primary=True).first()
        if primary and primary.image:
            return primary.image.url
        first_img = product.images.first()
        return first_img.image.url if first_img else None