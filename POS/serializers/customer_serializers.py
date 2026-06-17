from rest_framework import serializers
from ..models import (
    CustomerProfile, CustomerGroup, CustomerLedger, Address,
    WalletTransaction, LoyaltyPoints, LoyaltyTransaction,
    Wishlist, CompareList
)


class CustomerGroupSerializer(serializers.ModelSerializer):
    customer_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomerGroup
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_customer_count(self, obj):
        return obj.customers.count()


class CustomerProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields = [
            'customer_id', 'total_orders', 'total_spent', 'total_returns',
            'wallet_balance', 'loyalty_points', 'created_at', 'updated_at'
        ]


class CustomerProfileListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user_email', 'customer_id', 'phone', 'group',
            'total_orders', 'total_spent', 'wallet_balance',
            'referral_code', 'created_at'
        ]


class CustomerLedgerSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source='customer.email', read_only=True)

    class Meta:
        model = CustomerLedger
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = WalletTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LoyaltyPointsSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LoyaltyPoints
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_product_image(self, obj):
        primary = obj.product.images.filter(is_primary=True).first()
        return primary.image.url if primary else None


class CompareListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = CompareList
        fields = '__all__'
        read_only_fields = ['created_at']