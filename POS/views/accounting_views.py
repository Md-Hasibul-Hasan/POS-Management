from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsOwner, IsEmployeeOrReadOnly, IsOwnerOrManagerOrReadOnly

from ..models import AccountCategory, AccountTransaction, TaxConfiguration, FraudRule, IPBlacklist, AuditLog
from ..serializers import (
    AccountCategorySerializer, AccountTransactionSerializer,
    AccountTransactionListSerializer, TaxConfigurationSerializer,
    FraudRuleSerializer, IPBlacklistSerializer, AuditLogSerializer,
)


@extend_schema(tags=["Accounting - Categories"])
class AccountCategoryListCreateView(generics.ListCreateAPIView):
    queryset = AccountCategory.objects.all()
    serializer_class = AccountCategorySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category_type', 'is_system']
    search_fields = ['name', 'description']


@extend_schema(tags=["Accounting - Categories"])
class AccountCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AccountCategory.objects.all()
    serializer_class = AccountCategorySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Accounting - Transactions"])
class AccountTransactionListCreateView(generics.ListCreateAPIView):
    queryset = AccountTransaction.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'currency']
    search_fields = ['description', 'reference_type']
    ordering_fields = ['-transaction_date']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return AccountTransactionListSerializer
        return AccountTransactionSerializer


@extend_schema(tags=["Accounting - Transactions"])
class AccountTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AccountTransaction.objects.all()
    serializer_class = AccountTransactionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Accounting - Tax Configurations"])
class TaxConfigurationListCreateView(generics.ListCreateAPIView):
    queryset = TaxConfiguration.objects.all()
    serializer_class = TaxConfigurationSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'is_default', 'tax_type']
    search_fields = ['name']


@extend_schema(tags=["Accounting - Tax Configurations"])
class TaxConfigurationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaxConfiguration.objects.all()
    serializer_class = TaxConfigurationSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Accounting - Fraud Rules"])
class FraudRuleListCreateView(generics.ListCreateAPIView):
    queryset = FraudRule.objects.all()
    serializer_class = FraudRuleSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rule_type', 'is_active']
    search_fields = ['name', 'description']


@extend_schema(tags=["Accounting - Fraud Rules"])
class FraudRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FraudRule.objects.all()
    serializer_class = FraudRuleSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Accounting - IP Blacklist"])
class IPBlacklistListCreateView(generics.ListCreateAPIView):
    queryset = IPBlacklist.objects.all()
    serializer_class = IPBlacklistSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['ip_address', 'reason']


@extend_schema(tags=["Accounting - IP Blacklist"])
class IPBlacklistDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IPBlacklist.objects.all()
    serializer_class = IPBlacklistSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Accounting - Audit Logs"])
class AuditLogListCreateView(generics.ListCreateAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'module']
    search_fields = ['user__email', 'action_type', 'module', 'object_repr']
    ordering_fields = ['-created_at']


@extend_schema(tags=["Accounting - Audit Logs"])
class AuditLogDetailView(generics.RetrieveDestroyAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]