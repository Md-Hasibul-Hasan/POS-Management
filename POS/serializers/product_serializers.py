from rest_framework import serializers
from ..models import Product, ProductVariant, VariantAttribute, ProductImage, ProductVideo
from ..services import ProductService
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
        return ProductService.get_variant_final_price(obj)


class ProductVariantListSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'is_default', 'base_price', 'selling_price',
            'stock', 'reserved_stock', 'image', 'final_price', 'created_at'
        ]

    def get_final_price(self, obj):
        return ProductService.get_variant_final_price(obj)


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
        return ProductService.get_product_primary_image(obj)

    def get_final_price(self, obj):
        if obj.has_variants:
            return None
        return ProductService.get_product_final_price(obj)


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
        return ProductService.get_product_final_price(obj)


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = [
            'selling_price', 'stock_status', 'total_units_sold',
            'total_revenue', 'average_rating', 'total_reviews',
            'created_at', 'updated_at', 'deleted_at'
        ]

    def validate_sku(self, value):
        """Check SKU uniqueness at serializer level (better error than DB IntegrityError)."""
        from ..models import Product
        if Product.all_objects.filter(sku=value).exists():
            raise serializers.ValidationError(f"Product with SKU '{value}' already exists.")
        return value

    def validate_barcode(self, value):
        """Check barcode uniqueness if provided."""
        if value:
            from ..models import Product
            if Product.all_objects.filter(barcode=value).exists():
                raise serializers.ValidationError(f"Product with barcode '{value}' already exists.")
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)