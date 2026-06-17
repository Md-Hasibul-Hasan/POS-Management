from rest_framework import serializers
from ..models import Country, Division, District, Area, CourierProvider, ShippingZone, ShippingRate


class CountrySerializer(serializers.ModelSerializer):
    division_count = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_division_count(self, obj):
        return obj.divisions.count()


class DivisionSerializer(serializers.ModelSerializer):
    district_count = serializers.SerializerMethodField()

    class Meta:
        model = Division
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_district_count(self, obj):
        return obj.districts.count()


class DistrictSerializer(serializers.ModelSerializer):
    area_count = serializers.SerializerMethodField()

    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_area_count(self, obj):
        return obj.areas.count()


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CourierProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourierProvider
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ShippingZoneSerializer(serializers.ModelSerializer):
    area_count = serializers.SerializerMethodField()

    class Meta:
        model = ShippingZone
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_area_count(self, obj):
        return obj.areas.count()


class ShippingRateSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='shipping_zone.name', read_only=True)
    courier_name = serializers.CharField(source='courier_provider.name', read_only=True)

    class Meta:
        model = ShippingRate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']