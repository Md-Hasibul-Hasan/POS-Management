# =============================================================================
#  GEOGRAPHY & SHIPPING
# =============================================================================

from django.db import models

from .common import BaseModel


class Country(BaseModel):
    name = models.CharField(max_length=255)
    iso_code = models.CharField(max_length=3, unique=True)
    phone_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'countries'

    def __str__(self):
        return self.name


class Division(BaseModel):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='divisions')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['country', 'name'], name='unique_division_per_country')]

    def __str__(self):
        return self.name


class District(BaseModel):
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['division', 'name'], name='unique_district_per_division')]

    def __str__(self):
        return self.name


class Area(BaseModel):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['district', 'name'], name='unique_area_per_district')]

    def __str__(self):
        return self.name


class CourierProvider(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    tracking_url = models.URLField(null=True, blank=True)
    api_configuration = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class ShippingZone(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    districts = models.ManyToManyField(District, blank=True, related_name='shipping_zones')
    areas = models.ManyToManyField(Area, blank=True, related_name='shipping_zones')
    estimated_delivery_days = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class ShippingRate(BaseModel):
    shipping_zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name='rates')
    courier_provider = models.ForeignKey(CourierProvider, on_delete=models.CASCADE, related_name='rates')
    shipping_class = models.CharField(max_length=100, null=True, blank=True)
    min_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    per_kg_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cod_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    free_shipping_threshold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    estimated_days = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.shipping_zone.name} - {self.courier_provider.name}"