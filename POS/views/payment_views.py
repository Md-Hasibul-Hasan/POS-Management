from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsEmployeeOrReadOnly, IsOwnerOrManagerOrReadOnly

from ..models import PaymentGateway, PaymentMethod, PaymentSession, Payment, RefundTransaction, PaymentEventLog
from ..serializers import (
    PaymentGatewaySerializer, PaymentMethodSerializer,
    PaymentSessionSerializer, PaymentSerializer, PaymentListSerializer,
    RefundTransactionSerializer, PaymentEventLogSerializer,
)


@extend_schema(tags=["Payments - Gateways"])
class PaymentGatewayListCreateView(generics.ListCreateAPIView):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['gateway_type', 'is_active']
    search_fields = ['name', 'code']


@extend_schema(tags=["Payments - Gateways"])
class PaymentGatewayDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Payments - Methods"])
class PaymentMethodListCreateView(generics.ListCreateAPIView):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['gateway', 'payment_type', 'is_active']


@extend_schema(tags=["Payments - Methods"])
class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Payments - Sessions"])
class PaymentSessionListCreateView(generics.ListCreateAPIView):
    queryset = PaymentSession.objects.all()
    serializer_class = PaymentSessionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session_status', 'order']


@extend_schema(tags=["Payments - Sessions"])
class PaymentSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PaymentSession.objects.all()
    serializer_class = PaymentSessionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Payments"])
class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_channel', 'is_cod', 'is_flagged']
    search_fields = ['order__order_number', 'user__email', 'gateway_transaction_id']
    ordering_fields = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return PaymentListSerializer
        return PaymentSerializer


@extend_schema(tags=["Payments"])
class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Payments - Refunds"])
class RefundTransactionListCreateView(generics.ListCreateAPIView):
    queryset = RefundTransaction.objects.all()
    serializer_class = RefundTransactionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment']


@extend_schema(tags=["Payments - Event Logs"])
class PaymentEventLogListCreateView(generics.ListCreateAPIView):
    queryset = PaymentEventLog.objects.all()
    serializer_class = PaymentEventLogSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'payment']