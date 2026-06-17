from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsEmployeeOrReadOnly, IsOwnerOrManagerOrReadOnly

from ..models import (
    Supplier, SupplierLedger, Purchase, PurchaseItem, PurchasePayment,
    InventoryBatch, InventoryTransaction, StockReservation,
    DamageReport, LostInventory, StockAdjustment, SupplierReturn, StockAudit
)
from ..serializers import (
    SupplierSerializer, SupplierLedgerSerializer,
    PurchaseSerializer, PurchaseListSerializer,
    PurchaseItemSerializer, PurchasePaymentSerializer,
    InventoryBatchSerializer, InventoryTransactionSerializer,
    StockReservationSerializer, DamageReportSerializer,
    LostInventorySerializer, StockAdjustmentSerializer,
    SupplierReturnSerializer, StockAuditSerializer,
)


@extend_schema(tags=["Inventory - Suppliers"])
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'company_name', 'email', 'phone']


@extend_schema(tags=["Inventory - Suppliers"])
class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Inventory - Supplier Ledger"])
class SupplierLedgerListCreateView(generics.ListCreateAPIView):
    queryset = SupplierLedger.objects.all()
    serializer_class = SupplierLedgerSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['supplier', 'transaction_type']


@extend_schema(tags=["Inventory - Purchases"])
class PurchaseListCreateView(generics.ListCreateAPIView):
    queryset = Purchase.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'approval_status', 'supplier']
    search_fields = ['invoice_number', 'supplier__name']
    ordering_fields = ['-purchase_date']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return PurchaseListSerializer
        return PurchaseSerializer


@extend_schema(tags=["Inventory - Purchases"])
class PurchaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Inventory - Purchase Items"])
class PurchaseItemListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseItem.objects.all()
    serializer_class = PurchaseItemSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['purchase', 'product']


@extend_schema(tags=["Inventory - Purchase Payments"])
class PurchasePaymentListCreateView(generics.ListCreateAPIView):
    queryset = PurchasePayment.objects.all()
    serializer_class = PurchasePaymentSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['purchase']


@extend_schema(tags=["Inventory - Batches"])
class InventoryBatchListCreateView(generics.ListCreateAPIView):
    queryset = InventoryBatch.objects.all()
    serializer_class = InventoryBatchSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['batch_number', 'product__name']


@extend_schema(tags=["Inventory - Batches"])
class InventoryBatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryBatch.objects.all()
    serializer_class = InventoryBatchSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Inventory - Transactions"])
class InventoryTransactionListCreateView(generics.ListCreateAPIView):
    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['transaction_type', 'source_type', 'product', 'is_reversed']
    search_fields = ['product__name', 'source_document']


@extend_schema(tags=["Inventory - Reservations"])
class StockReservationListCreateView(generics.ListCreateAPIView):
    queryset = StockReservation.objects.all()
    serializer_class = StockReservationSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'reservation_source', 'product']


@extend_schema(tags=["Inventory - Damage"])
class DamageReportListCreateView(generics.ListCreateAPIView):
    queryset = DamageReport.objects.all()
    serializer_class = DamageReportSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']


@extend_schema(tags=["Inventory - Lost"])
class LostInventoryListCreateView(generics.ListCreateAPIView):
    queryset = LostInventory.objects.all()
    serializer_class = LostInventorySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']


@extend_schema(tags=["Inventory - Adjustments"])
class StockAdjustmentListCreateView(generics.ListCreateAPIView):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']


@extend_schema(tags=["Inventory - Supplier Returns"])
class SupplierReturnListCreateView(generics.ListCreateAPIView):
    queryset = SupplierReturn.objects.all()
    serializer_class = SupplierReturnSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['supplier', 'purchase']


@extend_schema(tags=["Inventory - Audits"])
class StockAuditListCreateView(generics.ListCreateAPIView):
    queryset = StockAudit.objects.all()
    serializer_class = StockAuditSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'product']