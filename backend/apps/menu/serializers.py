from rest_framework import serializers
from .models import Category, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'image', 'image_url', 'price', 'food_type', 'is_popular',
            'is_special', 'is_available', 'preparation_time', 'calories',
            'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'restaurant', 'name', 'description', 'icon', 'image',
            'image_url', 'sort_order', 'is_active', 'items', 'item_count', 'created_at'
        ]
        read_only_fields = ['created_at']

    def get_item_count(self, obj):
        return obj.items.filter(is_available=True).count()

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class CategoryListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'restaurant', 'name', 'description', 'icon', 'image_url', 'sort_order', 'is_active', 'item_count']

    def get_item_count(self, obj):
        return obj.items.filter(is_available=True).count()

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
