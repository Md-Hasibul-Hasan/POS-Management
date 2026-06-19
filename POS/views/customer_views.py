from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsOwner

from ..models import (
    CustomerProfile, CustomerGroup, CustomerLedger, Address,
    WalletTransaction, LoyaltyPoints, LoyaltyTransaction,
    Wishlist, CompareList
)
from ..serializers import (
    CustomerProfileSerializer, CustomerProfileListSerializer,
    CustomerGroupSerializer, CustomerLedgerSerializer,
    AddressSerializer, WalletTransactionSerializer,
    LoyaltyPointsSerializer, LoyaltyTransactionSerializer,
    WishlistSerializer, CompareListSerializer,
)


@extend_schema(tags=["Customers - Profiles"])
class CustomerProfileListCreateView(generics.ListCreateAPIView):
    queryset = CustomerProfile.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'customer_id', 'phone']
    ordering_fields = ['created_at', 'total_orders', 'total_spent']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return CustomerProfileListSerializer
        return CustomerProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return CustomerProfile.objects.all()
        return CustomerProfile.objects.filter(user=user)


@extend_schema(tags=["Customers - Profiles"])
class CustomerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerProfileSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return CustomerProfile.objects.all()
        return CustomerProfile.objects.filter(user=user)


@extend_schema(tags=["Customers - Groups"])
class CustomerGroupListCreateView(generics.ListCreateAPIView):
    queryset = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Customers - Groups"])
class CustomerGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Customers - Ledger"])
class CustomerLedgerListCreateView(generics.ListCreateAPIView):
    queryset = CustomerLedger.objects.all()
    serializer_class = CustomerLedgerSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'transaction_type']


@extend_schema(tags=["Customers - Addresses"])
class AddressListCreateView(generics.ListCreateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user', 'address_type', 'is_default']

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return Address.objects.all()
        return Address.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Customers - Addresses"])
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return Address.objects.all()
        return Address.objects.filter(user=user)


@extend_schema(tags=["Customers - Wallet"])
class WalletTransactionListCreateView(generics.ListCreateAPIView):
    queryset = WalletTransaction.objects.all()
    serializer_class = WalletTransactionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'transaction_type', 'status']


@extend_schema(tags=["Customers - Loyalty"])
class LoyaltyPointsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LoyaltyPoints.objects.all()
    serializer_class = LoyaltyPointsSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return LoyaltyPoints.objects.all()
        return LoyaltyPoints.objects.filter(user=user)


@extend_schema(tags=["Customers - Loyalty"])
class LoyaltyTransactionListCreateView(generics.ListCreateAPIView):
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'transaction_type']

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return LoyaltyTransaction.objects.all()
        return LoyaltyTransaction.objects.filter(user=user)


@extend_schema(tags=["Customers - Wishlist"])
class WishlistListCreateView(generics.ListCreateAPIView):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return Wishlist.objects.all()
        return Wishlist.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Customers - Wishlist"])
class WishlistDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return Wishlist.objects.all()
        return Wishlist.objects.filter(user=user)


@extend_schema(tags=["Customers - Compare List"])
class CompareListListCreateView(generics.ListCreateAPIView):
    queryset = CompareList.objects.all()
    serializer_class = CompareListSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return CompareList.objects.all()
        return CompareList.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Customers - Compare List"])
class CompareListDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CompareList.objects.all()
    serializer_class = CompareListSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('owner', 'manager', 'salesman') or user.is_superuser or user.role == 'admin':
            return CompareList.objects.all()
        return CompareList.objects.filter(user=user)