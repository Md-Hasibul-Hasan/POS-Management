from rest_framework import serializers
from ..models import Campaign, Coupon, CouponUsage, Banner, StoreSettings, NotificationTemplate, Notification


class CampaignSerializer(serializers.ModelSerializer):
    is_running = serializers.BooleanField(read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ['current_usage', 'created_at', 'updated_at']


class CampaignListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'slug', 'campaign_type', 'discount_type',
            'discount_value', 'is_active', 'is_featured', 'priority',
            'start_date', 'end_date', 'current_usage', 'usage_limit'
        ]


class CouponSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = '__all__'
        read_only_fields = ['current_usage', 'created_at', 'updated_at']


class CouponUsageSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model = CouponUsage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BannerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'image', 'mobile_image', 'link_type',
            'sort_order', 'is_active', 'is_popup', 'start_date', 'end_date'
        ]


class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at']