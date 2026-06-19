from rest_framework import generics, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsPublicReadEmployeeWrite

from ..models import Product, ProductVariant, ProductImage, ProductVideo
from ..serializers import (
    ProductSerializer, ProductListSerializer, ProductCreateSerializer,
    ProductVariantSerializer, ProductImageSerializer, ProductVideoSerializer,
)
from .mixins import PublicListMixin, EmployeeListMixin


@extend_schema(tags=["Products"])
class ProductListCreateView(PublicListMixin, generics.ListCreateAPIView):
    queryset = Product.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsPublicReadEmployeeWrite]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'status', 'approval_status', 'stock_status',
                        'is_featured', 'is_special', 'is_trending', 'has_variants']
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering_fields = ['created_at', 'name', 'base_price', 'selling_price']
    select_related_fields = ['category', 'brand', 'unit']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["Products"])
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsPublicReadEmployeeWrite]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Products - Variants"])
class ProductVariantListCreateView(PublicListMixin, generics.ListCreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsPublicReadEmployeeWrite]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'is_default']
    search_fields = ['name', 'sku']
    select_related_fields = ['product']


@extend_schema(tags=["Products - Variants"])
class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsPublicReadEmployeeWrite]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Products - Images"])
class ProductImageListCreateView(EmployeeListMixin, generics.ListCreateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    parser_classes = [MultiPartParser, FormParser]


@extend_schema(tags=["Products - Images"])
class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]
    parser_classes = [MultiPartParser, FormParser]


@extend_schema(tags=["Products - Videos"])
class ProductVideoListCreateView(EmployeeListMixin, generics.ListCreateAPIView):
    queryset = ProductVideo.objects.all()
    serializer_class = ProductVideoSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Products - Videos"])
class ProductVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductVideo.objects.all()
    serializer_class = ProductVideoSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployee]
    renderer_classes = [UserRenderer]