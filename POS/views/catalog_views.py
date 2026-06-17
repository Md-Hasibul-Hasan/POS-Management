from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsEmployeeOrReadOnly, IsOwnerOrManagerOrReadOnly

from ..models import Category, Brand, Unit, Tag, Attribute, AttributeValue, ProductFAQ, ProductReview
from ..serializers import (
    CategorySerializer, CategoryListSerializer,
    BrandSerializer, BrandListSerializer,
    UnitSerializer, TagSerializer,
    AttributeSerializer, AttributeValueSerializer,
    ProductFAQSerializer, ProductReviewSerializer,
)


@extend_schema(tags=["Catalog - Categories"])
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return CategoryListSerializer
        return CategorySerializer


@extend_schema(tags=["Catalog - Categories"])
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Brands"])
class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'pk' not in self.kwargs:
            return BrandListSerializer
        return BrandSerializer


@extend_schema(tags=["Catalog - Brands"])
class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Units"])
class UnitListCreateView(generics.ListCreateAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Units"])
class UnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Tags"])
class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Tags"])
class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Attributes"])
class AttributeListCreateView(generics.ListCreateAPIView):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Attributes"])
class AttributeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Attribute Values"])
class AttributeValueListCreateView(generics.ListCreateAPIView):
    queryset = AttributeValue.objects.all()
    serializer_class = AttributeValueSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Attribute Values"])
class AttributeValueDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AttributeValue.objects.all()
    serializer_class = AttributeValueSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - FAQs"])
class ProductFAQListCreateView(generics.ListCreateAPIView):
    queryset = ProductFAQ.objects.all()
    serializer_class = ProductFAQSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - FAQs"])
class ProductFAQDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductFAQ.objects.all()
    serializer_class = ProductFAQSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Catalog - Reviews"])
class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    search_fields = ['product__name', 'user__email', 'title', 'comment']
    ordering_fields = ['rating', 'created_at']


@extend_schema(tags=["Catalog - Reviews"])
class ProductReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]