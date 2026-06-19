from rest_framework import serializers
from ..models import Order, OrderItem, OrderStatusLog, OrderCoupon, Cart, CartItem
from ..models import ReturnRecord, ReturnItem, ReturnInspection, ExchangeRequest, Shipment
from ..services import OrderService


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.name', read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = '__all__'


class OrderCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderCoupon
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OrderListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'invoice_number', 'user_email', 'user_name',
            'source', 'status', 'payment_status', 'fulfillment_status',
            'total_amount', 'currency', 'is_flagged', 'fraud_score',
            'item_count', 'created_at'
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = [
            'order_number', 'invoice_number', 'fraud_score', 'risk_level',
            'is_flagged', 'created_at', 'updated_at', 'confirmed_at',
            'delivered_at', 'cancelled_at', 'returned_at'
        ]

    def validate_coupons(self, value):
        """Validate and compute coupon discount at the order level.
        Delegates to OrderService to keep business logic in services.
        """
        request = self.context.get('request')
        if request and request.method in ('POST', 'PUT', 'PATCH'):
            subtotal = request.data.get('subtotal', 0)
            from decimal import Decimal
            subtotal = Decimal(str(subtotal))
            try:
                OrderService.validate_coupons_for_order(subtotal, value)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        cart_item = super().create(validated_data)
        OrderService.recalculate_cart_totals(cart_item.cart)
        return cart_item

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        OrderService.recalculate_cart_totals(instance.cart)
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ReturnItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnItem
        fields = '__all__'


class ReturnInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnInspection
        fields = '__all__'


class ReturnRecordSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True, read_only=True)

    class Meta:
        model = ReturnRecord
        fields = '__all__'
        read_only_fields = ['approved_by', 'approved_at', 'created_at', 'updated_at']


class ExchangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ['courier_response', 'created_at', 'updated_at']