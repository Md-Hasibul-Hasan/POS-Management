from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from Authentication.authentication import SessionJWTAuthentication
from Authentication.renderers import UserRenderer
from Authentication.permissions import IsEmployee, IsOwnerOrManager, IsEmployeeOrReadOnly, IsOwnerOrManagerOrReadOnly

from ..models import Country, Division, District, Area, CourierProvider, ShippingZone, ShippingRate
from ..serializers import (
    CountrySerializer, DivisionSerializer, DistrictSerializer,
    AreaSerializer, CourierProviderSerializer,
    ShippingZoneSerializer, ShippingRateSerializer,
)


@extend_schema(tags=["Geo - Countries"])
class CountryListCreateView(generics.ListCreateAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'iso_code']


@extend_schema(tags=["Geo - Countries"])
class CountryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Geo - Divisions"])
class DivisionListCreateView(generics.ListCreateAPIView):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['country']
    search_fields = ['name', 'code']


@extend_schema(tags=["Geo - Divisions"])
class DivisionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Geo - Districts"])
class DistrictListCreateView(generics.ListCreateAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['division']
    search_fields = ['name', 'code']


@extend_schema(tags=["Geo - Districts"])
class DistrictDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Geo - Areas"])
class AreaListCreateView(generics.ListCreateAPIView):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['district']
    search_fields = ['name', 'postal_code']


@extend_schema(tags=["Geo - Areas"])
class AreaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Geo - Courier Providers"])
class CourierProviderListCreateView(generics.ListCreateAPIView):
    queryset = CourierProvider.objects.all()
    serializer_class = CourierProviderSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code']


@extend_schema(tags=["Geo - Courier Providers"])
class CourierProviderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CourierProvider.objects.all()
    serializer_class = CourierProviderSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Geo - Shipping Zones"])
class ShippingZoneListCreateView(generics.ListCreateAPIView):
    queryset = ShippingZone.objects.all()
    serializer_class = ShippingZoneSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code']


@extend_schema(tags=["Geo - Shipping Zones"])
class ShippingZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ShippingZone.objects.all()
    serializer_class = ShippingZoneSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]


@extend_schema(tags=["Geo - Shipping Rates"])
class ShippingRateListCreateView(generics.ListCreateAPIView):
    queryset = ShippingRate.objects.all()
    serializer_class = ShippingRateSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['shipping_zone', 'courier_provider']
    search_fields = ['shipping_zone__name', 'courier_provider__name']


@extend_schema(tags=["Geo - Shipping Rates"])
class ShippingRateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ShippingRate.objects.all()
    serializer_class = ShippingRateSerializer
    authentication_classes = [SessionJWTAuthentication]
    permission_classes = [IsEmployeeOrReadOnly]
    renderer_classes = [UserRenderer]