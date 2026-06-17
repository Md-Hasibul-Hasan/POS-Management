from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsOwnerOrManagerOrReadOnly, IsEmployeeOrReadOnly

from ..models import Campaign, Coupon, CouponUsage, Banner, StoreSettings, NotificationTemplate, Notification
from ..serializers import (
    CampaignSerializer, CampaignListSerializer,
    CouponSerializer, CouponUsageSerializer,
    BannerSerializer, BannerListSerializer,
    StoreSettingsSerializer, NotificationTemplateSerializer, NotificationSerializer,
)


@extend_schema(tags=["Marketing - Campaigns"])
class CampaignListCreateView(generics.ListCreateAPIView):
    queryset = Campaign.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['campaign_type', 'discount_type', 'is_active', 'is_featured']
    search_fields = ['name', 'slug', 'description']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return CampaignListSerializer
        return CampaignSerializer


@extend_schema(tags=["Marketing - Campaigns"])
class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Marketing - Coupons"])
class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['coupon_category', 'discount_type', 'is_active']
    search_fields = ['code', 'title']


@extend_schema(tags=["Marketing - Coupons"])
class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Marketing - Coupon Usage"])
class CouponUsageListCreateView(generics.ListCreateAPIView):
    queryset = CouponUsage.objects.all()
    serializer_class = CouponUsageSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['coupon', 'status']


@extend_schema(tags=["Marketing - Banners"])
class BannerListCreateView(generics.ListCreateAPIView):
    queryset = Banner.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['link_type', 'is_active', 'is_popup']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return BannerListSerializer
        return BannerSerializer


@extend_schema(tags=["Marketing - Banners"])
class BannerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Marketing - Store Settings"])
class StoreSettingsListCreateView(generics.ListCreateAPIView):
    queryset = StoreSettings.objects.all()
    serializer_class = StoreSettingsSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Marketing - Store Settings"])
class StoreSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StoreSettings.objects.all()
    serializer_class = StoreSettingsSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManager]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Marketing - Notifications"])
class NotificationListCreateView(generics.ListCreateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'delivery_channel', 'is_read', 'user']


@extend_schema(tags=["Marketing - Notifications"])
class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Marketing - Notification Templates"])
class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template_type']


@extend_schema(tags=["Marketing - Notification Templates"])
class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsOwnerOrManagerOrReadOnly]
    renderer_classes = [UserRenderer]