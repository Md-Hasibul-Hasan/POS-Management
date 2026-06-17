from rest_framework import serializers
from ..models import (
    Supplier, SupplierLedger, Purchase, PurchaseItem, PurchasePayment,
    InventoryBatch, InventoryTransaction, StockReservation,
    DamageReport, LostInventory, StockAdjustment, SupplierReturn, StockAudit
)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SupplierLedgerSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = SupplierLedger
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PurchasePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasePayment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PurchaseListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'invoice_number', 'supplier_name', 'total_amount',
            'paid_amount', 'due_amount', 'status', 'approval_status',
            'purchase_date', 'created_at'
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    payments = PurchasePaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ['due_amount', 'created_at', 'updated_at']


class InventoryBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = InventoryBatch
        fields = '__all__'
        read_only_fields = ['received_quantity', 'remaining_quantity', 'created_at', 'updated_at']


class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.name', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = '__all__'
        read_only_fields = [
            'previous_stock', 'new_stock', 'is_reversed',
            'reversed_transaction', 'created_at', 'updated_at'
        ]


class StockReservationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StockReservation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DamageReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source='reported_by.name', read_only=True)

    class Meta:
        model = DamageReport
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LostInventorySerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source='reported_by.name', read_only=True)

    class Meta:
        model = LostInventory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StockAdjustmentSerializer(serializers.ModelSerializer):
    adjusted_by_name = serializers.CharField(source='adjusted_by.name', read_only=True)

    class Meta:
        model = StockAdjustment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SupplierReturnSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = SupplierReturn
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StockAuditSerializer(serializers.ModelSerializer):
    audited_by_name = serializers.CharField(source='audited_by.name', read_only=True)

    class Meta:
        model = StockAudit
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']