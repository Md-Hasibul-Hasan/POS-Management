"""
POS Views — Thin CRUD views for POS operations.
All business logic lives in services (pos_service, register_service, shift_service).
Views handle: authentication, permissions, request/response, and service calls.
"""

from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager

from ..models import POSTerminal, POSShift, CashRegister, CashMovement
from ..serializers import (
    POSTerminalSerializer, POSTerminalListSerializer,
    POSShiftSerializer, POSShiftListSerializer,
    CashRegisterSerializer, CashRegisterListSerializer,
    CashMovementSerializer, CashMovementListSerializer,
)
from ..services import POSService, ShiftService, RegisterService


# =============================================================================
#  POS TERMINALS
# =============================================================================

@extend_schema(tags=["POS - Terminals"])
class POSTerminalListCreateView(generics.ListCreateAPIView):
    queryset = POSTerminal.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'terminal_code', 'location']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return POSTerminalListSerializer
        return POSTerminalSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["POS - Terminals"])
class POSTerminalDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = POSTerminal.objects.all()
    serializer_class = POSTerminalSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


# =============================================================================
#  POS SHIFTS
# =============================================================================

@extend_schema(tags=["POS - Shifts"])
class POSShiftListCreateView(generics.ListCreateAPIView):
    queryset = POSShift.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'terminal', 'cashier']
    search_fields = ['terminal__name', 'cashier__email']
    ordering_fields = ['-opening_time']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return POSShiftListSerializer
        return POSShiftSerializer


@extend_schema(tags=["POS - Shifts"])
class POSShiftDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = POSShift.objects.all()
    serializer_class = POSShiftSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["POS - Shifts"])
class POSShiftStartView(generics.CreateAPIView):
    """
    Start a new shift.
    POST with: terminal_id, cashier_id, opening_note (optional), opening_balance (optional).
    Delegates to ShiftService.start_shift().
    """
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]

    def post(self, request, *args, **kwargs):
        terminal_id = request.data.get('terminal_id')
        opening_note = request.data.get('opening_note', '')
        opening_balance = request.data.get('opening_balance', 0)

        from ..models import POSTerminal
        try:
            terminal = POSTerminal.objects.get(id=terminal_id, is_active=True)
        except POSTerminal.DoesNotExist:
            return Response(
                {'error': 'Active terminal not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = ShiftService.start_shift(
                terminal=terminal,
                cashier=request.user,
                opening_note=opening_note,
                opening_balance=opening_balance,
                created_by=request.user,
            )
            return Response({
                'shift': POSShiftSerializer(result['shift']).data,
                'register': CashRegisterSerializer(result['register']).data,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["POS - Shifts"])
class POSShiftEndView(generics.CreateAPIView):
    """
    End an open shift.
    POST with: shift_id, actual_closing_balance, closing_note (optional).
    Delegates to ShiftService.end_shift().
    """
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]

    def post(self, request, *args, **kwargs):
        shift_id = request.data.get('shift_id')
        actual_closing_balance = request.data.get('actual_closing_balance')
        closing_note = request.data.get('closing_note', '')

        try:
            shift = POSShift.objects.get(id=shift_id)
        except POSShift.DoesNotExist:
            return Response(
                {'error': 'Shift not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = ShiftService.end_shift(
                shift=shift,
                actual_closing_balance=actual_closing_balance,
                closing_note=closing_note,
                closed_by=request.user,
            )
            return Response({
                'shift': POSShiftSerializer(result['shift']).data,
                'register': CashRegisterSerializer(result['register']).data,
                'discrepancy': str(result['discrepancy']) if result['discrepancy'] is not None else None,
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
#  CASH REGISTERS
# =============================================================================

@extend_schema(tags=["POS - Registers"])
class CashRegisterListCreateView(generics.ListCreateAPIView):
    queryset = CashRegister.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'terminal']
    ordering_fields = ['-opened_at']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return CashRegisterListSerializer
        return CashRegisterSerializer


@extend_schema(tags=["POS - Registers"])
class CashRegisterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CashRegister.objects.all()
    serializer_class = CashRegisterSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["POS - Registers"])
class CashRegisterReconcileView(generics.CreateAPIView):
    """
    Reconcile a cash register.
    POST with: register_id.
    Delegates to RegisterService.reconcile_register().
    """
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]

    def post(self, request, *args, **kwargs):
        register_id = request.data.get('register_id')
        try:
            register = CashRegister.objects.get(id=register_id)
        except CashRegister.DoesNotExist:
            return Response(
                {'error': 'Register not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            RegisterService.reconcile_register(register)
            return Response({
                'register': CashRegisterSerializer(register).data,
                'message': 'Register reconciled successfully.',
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
#  CASH MOVEMENTS
# =============================================================================

@extend_schema(tags=["POS - Cash Movements"])
class CashMovementListCreateView(generics.ListCreateAPIView):
    queryset = CashMovement.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['movement_type', 'register', 'shift']
    search_fields = ['note', 'reference']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return CashMovementListSerializer
        return CashMovementSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["POS - Cash Movements"])
class CashMovementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CashMovement.objects.all()
    serializer_class = CashMovementSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]