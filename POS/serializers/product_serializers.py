from rest_framework import serializers
from ..models import Product, ProductVariant, VariantAttribute, ProductImage, ProductVideo
from ..services import PricingEngine
from .catalog_serializers import CategoryListSerializer, BrandSerializer


class VariantAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantAttribute
        fields = '__all__'


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = VariantAttributeSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = ['attribute_signature', 'selling_price', 'created_at', 'updated_at']

    def get_final_price(self, obj):
        """Compute final price including campaign discounts at read time."""
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(obj.product)
        result = PricingEngine.calculate_variant_price(
            obj,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        result['campaign_id'] = campaign.id if campaign else None
        return result


class ProductVariantListSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'is_default', 'base_price', 'selling_price',
            'stock', 'reserved_stock', 'image', 'final_price', 'created_at'
        ]

    def get_final_price(self, obj):
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(obj.product)
        result = PricingEngine.calculate_variant_price(
            obj,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        result['campaign_id'] = campaign.id if campaign else None
        return result


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'


class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = '__all__'


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    image = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'category_name', 'brand_name',
            'base_price', 'selling_price', 'stock_status', 'status',
            'is_featured', 'is_special', 'is_trending', 'has_variants',
            'image', 'final_price', 'created_at'
        ]

    def get_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary and primary.image:
            return primary.image.url
        first_img = obj.images.first()
        return first_img.image.url if first_img else None

    def get_final_price(self, obj):
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(obj)
        result = PricingEngine.calculate_product_price(
            obj,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        result['campaign_id'] = campaign.id if campaign else None
        return result


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    variants = ProductVariantListSerializer(many=True, read_only=True)
    category_detail = CategoryListSerializer(source='category', read_only=True)
    brand_detail = BrandSerializer(source='brand', read_only=True)
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = [
            'selling_price', 'stock_status', 'total_units_sold',
            'total_revenue', 'average_rating', 'total_reviews',
            'created_at', 'updated_at', 'created_by'
        ]

    def get_final_price(self, obj):
        if obj.has_variants:
            return None  # Variants have their own final_price
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(obj)
        result = PricingEngine.calculate_product_price(
            obj,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        result['campaign_id'] = campaign.id if campaign else None
        return result


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = [
            'selling_price', 'stock_status', 'total_units_sold',
            'total_revenue', 'average_rating', 'total_reviews',
            'created_at', 'updated_at', 'deleted_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)