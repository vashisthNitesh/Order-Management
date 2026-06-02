from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    restaurant = serializers.SerializerMethodField()
    restaurant_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'role', 'restaurant', 'restaurant_id']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'admin'
        try:
            return obj.staff_profile.role
        except AttributeError:
            return 'staff'

    def get_restaurant(self, obj):
        try:
            return obj.staff_profile.restaurant.name
        except AttributeError:
            return None

    def get_restaurant_id(self, obj):
        try:
            return obj.staff_profile.restaurant.id
        except AttributeError:
            return None
