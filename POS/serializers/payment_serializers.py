from rest_framework import serializers
from ..models import PaymentGateway, PaymentMethod, PaymentSession, Payment, RefundTransaction, PaymentEventLog


class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PaymentMethodSerializer(serializers.ModelSerializer):
    gateway_name = serializers.CharField(source='gateway.name', read_only=True)

    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PaymentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSession
        fields = '__all__'
        read_only_fields = ['raw_session_response', 'created_at', 'updated_at']


class PaymentListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order_number', 'user_email', 'amount', 'currency',
            'status', 'payment_method', 'payment_channel',
            'is_cod', 'is_flagged', 'fraud_score',
            'paid_at', 'created_at'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'fraud_score', 'risk_level', 'is_flagged',
            'paid_at', 'created_at', 'updated_at'
        ]


class RefundTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PaymentEventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentEventLog
        fields = '__all__'
        read_only_fields = ['created_at']