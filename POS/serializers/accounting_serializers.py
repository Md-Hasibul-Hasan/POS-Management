from rest_framework import serializers
from ..models import AccountCategory, AccountTransaction, TaxConfiguration, FraudRule, IPBlacklist, AuditLog


class AccountCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountCategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AccountTransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = AccountTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AccountTransactionListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = AccountTransaction
        fields = [
            'id', 'category_name', 'transaction_date', 'amount',
            'currency', 'description', 'reference_type', 'created_at'
        ]


class TaxConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxConfiguration
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class FraudRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class IPBlacklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPBlacklist
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['created_at']