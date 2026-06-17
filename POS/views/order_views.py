from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsEmployeeOrReadOnly

from ..models import Order, OrderItem, Cart, CartItem, ReturnRecord, ExchangeRequest, Shipment
from ..serializers import (
    OrderSerializer, OrderListSerializer, OrderItemSerializer,
    CartSerializer, CartItemSerializer,
    ReturnRecordSerializer, ExchangeRequestSerializer, ShipmentSerializer,
)


@extend_schema(tags=["Orders"])
class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'fulfillment_status', 'source', 'is_flagged']
    search_fields = ['order_number', 'invoice_number', 'user__email']
    ordering_fields = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["Orders"])
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Orders - Items"])
class OrderItemListCreateView(generics.ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order']


@extend_schema(tags=["Carts"])
class CartListCreateView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'is_active']


@extend_schema(tags=["Carts"])
class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Carts - Items"])
class CartItemListCreateView(generics.ListCreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cart', 'product']


@extend_schema(tags=["Carts - Items"])
class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Returns"])
class ReturnRecordListCreateView(generics.ListCreateAPIView):
    queryset = ReturnRecord.objects.all()
    serializer_class = ReturnRecordSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'return_type', 'order']
    search_fields = ['order__order_number']


@extend_schema(tags=["Returns"])
class ReturnRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReturnRecord.objects.all()
    serializer_class = ReturnRecordSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Exchanges"])
class ExchangeRequestListCreateView(generics.ListCreateAPIView):
    queryset = ExchangeRequest.objects.all()
    serializer_class = ExchangeRequestSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'order']


@extend_schema(tags=["Exchanges"])
class ExchangeRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExchangeRequest.objects.all()
    serializer_class = ExchangeRequestSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Shipments"])
class ShipmentListCreateView(generics.ListCreateAPIView):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'order']
    search_fields = ['tracking_number']


@extend_schema(tags=["Shipments"])
class ShipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]