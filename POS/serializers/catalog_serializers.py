from rest_framework import serializers
from ..models import Category, Brand, Unit, Tag, Attribute, AttributeValue, ProductFAQ, ProductReview


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.products.count()


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'sort_order', 'image', 'created_at']


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.products.count()


class BrandListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'is_featured', 'sort_order']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    values_count = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = '__all__'

    def get_values_count(self, obj):
        return obj.values.count()


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = '__all__'


class ProductFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFAQ
        fields = '__all__'


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ProductReview
        fields = '__all__'
        read_only_fields = ['user', 'moderation_status', 'is_verified_purchase', 'created_at', 'updated_at']