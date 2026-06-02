from rest_framework import serializers
from .models import Restaurant, Table


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TableSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'restaurant', 'table_number', 'capacity', 'qr_code', 'qr_code_url', 'is_active', 'created_at']
        read_only_fields = ['qr_code', 'created_at']

    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if obj.qr_code and request:
            return request.build_absolute_uri(obj.qr_code.url)
        return None


class TableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['restaurant', 'table_number', 'capacity']

    def create(self, validated_data):
        table = Table(**validated_data)
        table.save()
        return table
