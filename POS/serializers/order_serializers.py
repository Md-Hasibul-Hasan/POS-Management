from rest_framework import serializers
from ..models import Order, OrderItem, OrderStatusLog, OrderCoupon, Cart, CartItem
from ..models import ReturnRecord, ReturnItem, ReturnInspection, ExchangeRequest, Shipment
from ..services import PricingEngine


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
        """Validate and compute coupon discount at the order level."""
        request = self.context.get('request')
        if request and request.method in ('POST', 'PUT', 'PATCH'):
            subtotal = self.initial_data.get('subtotal', 0)
            total_discount = 0
            for coupon in value:
                result = PricingEngine.apply_coupon_discount(
                    price_before_coupon=subtotal,
                    coupon=coupon,
                )
                total_discount += result['coupon_discount']
            # Cap discount at subtotal
            if total_discount > subtotal:
                raise serializers.ValidationError('Total coupon discount cannot exceed the subtotal.')
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_unit_price(self, obj):
        """Get the final price per unit (campaign → variant → product discount)."""
        if obj.variant:
            campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(obj.product)
            result = PricingEngine.calculate_variant_price(
                obj.variant,
                campaign_discount_value=disc_val,
                campaign_discount_type=disc_type,
            )
            return result['selling_price']
        # Non-variant product
        campaign, disc_val, disc_type = PricingEngine.find_best_campaign_for_product(obj.product)
        result = PricingEngine.calculate_product_price(
            obj.product,
            campaign_discount_value=disc_val,
            campaign_discount_type=disc_type,
        )
        return result['selling_price']

    def get_total_price(self, obj):
        unit = self.get_unit_price(obj)
        return unit * obj.quantity

    def create(self, validated_data):
        cart_item = super().create(validated_data)
        # Recalculate cart totals
        self._recalc_cart_totals(cart_item.cart)
        return cart_item

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._recalc_cart_totals(instance.cart)
        return instance

    def _recalc_cart_totals(self, cart):
        """Recalculate cart totals after any item mutation."""
        subtotal = 0
        discount_amount = 0
        for item in cart.items.all():
            unit = self.get_unit_price(item)
            subtotal += unit * item.quantity
            # Track product-level discount
            if item.product.discount_value > 0:
                discount_amount += item.product.discount_value * item.quantity
        cart.subtotal = subtotal
        cart.discount_amount = discount_amount
        cart.total_amount = max(subtotal - discount_amount, 0)
        cart.save(update_fields=['subtotal', 'discount_amount', 'total_amount'])


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