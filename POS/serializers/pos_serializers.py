"""
POS Serializers — Thin CRUD serializers for POS operations.
All business logic lives in services (pos_service, register_service, shift_service).
"""

from rest_framework import serializers
from ..models import POSTerminal, POSShift, CashRegister, CashMovement


class POSTerminalSerializer(serializers.ModelSerializer):
    shift_count = serializers.SerializerMethodField()

    class Meta:
        model = POSTerminal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_shift_count(self, obj):
        return obj.shifts.count()


class POSTerminalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSTerminal
        fields = ['id', 'name', 'terminal_code', 'location', 'is_active', 'created_at']


class POSShiftSerializer(serializers.ModelSerializer):
    cashier_name = serializers.SerializerMethodField()
    terminal_name = serializers.CharField(source='terminal.name', read_only=True)

    class Meta:
        model = POSShift
        fields = '__all__'
        read_only_fields = [
            'total_sales_amount', 'total_orders',
            'opening_time', 'closing_time', 'created_at', 'updated_at',
        ]

    def get_cashier_name(self, obj):
        return obj.cashier.get_full_name() or obj.cashier.username if obj.cashier else None


class POSShiftListSerializer(serializers.ModelSerializer):
    cashier_name = serializers.SerializerMethodField()
    terminal_name = serializers.CharField(source='terminal.name', read_only=True)

    class Meta:
        model = POSShift
        fields = [
            'id', 'terminal_name', 'cashier_name', 'status',
            'opening_time', 'closing_time',
            'total_sales_amount', 'total_orders', 'created_at',
        ]

    def get_cashier_name(self, obj):
        return obj.cashier.get_full_name() or obj.cashier.username if obj.cashier else None


class CashRegisterSerializer(serializers.ModelSerializer):
    terminal_name = serializers.CharField(source='terminal.name', read_only=True)
    discrepancy = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    shift_id = serializers.IntegerField(source='shift.id', read_only=True)

    class Meta:
        model = CashRegister
        fields = '__all__'
        read_only_fields = [
            'expected_closing_balance', 'actual_closing_balance',
            'opened_at', 'closed_at', 'created_at', 'updated_at',
        ]


class CashRegisterListSerializer(serializers.ModelSerializer):
    terminal_name = serializers.CharField(source='terminal.name', read_only=True)
    discrepancy = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = CashRegister
        fields = [
            'id', 'terminal_name', 'status',
            'opening_balance', 'expected_closing_balance',
            'actual_closing_balance', 'discrepancy',
            'opened_at', 'closed_at',
        ]


class CashMovementSerializer(serializers.ModelSerializer):
    register_id = serializers.IntegerField(source='register.id', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CashMovement
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username if obj.created_by else None


class CashMovementListSerializer(serializers.ModelSerializer):
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = CashMovement
        fields = [
            'id', 'movement_type', 'movement_type_display',
            'amount', 'note', 'reference', 'created_at',
        ]