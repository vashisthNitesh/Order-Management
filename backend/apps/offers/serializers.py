from rest_framework import serializers
from .models import Offer


class OfferSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    discount_display = serializers.CharField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'restaurant', 'title', 'description', 'image', 'image_url',
            'discount_type', 'discount_value', 'min_order_amount',
            'applicable_items', 'applicable_categories', 'start_date', 'end_date',
            'is_active', 'usage_limit', 'usage_count', 'promo_code',
            'is_valid', 'discount_display', 'created_at'
        ]
        read_only_fields = ['usage_count', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
