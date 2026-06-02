from rest_framework import serializers
from django.contrib.auth.models import User
from .models import StaffProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']


class StaffProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = ['id', 'user', 'full_name', 'restaurant', 'role', 'phone', 'avatar', 'is_active', 'created_at']
        read_only_fields = ['created_at']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class StaffCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    restaurant = serializers.PrimaryKeyRelatedField(queryset=__import__('apps.restaurants.models', fromlist=['Restaurant']).Restaurant.objects.all())
    role = serializers.ChoiceField(choices=StaffProfile.ROLE_CHOICES)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        restaurant = validated_data.pop('restaurant')
        role = validated_data.pop('role')
        phone = validated_data.pop('phone', '')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data, password=password)
        staff = StaffProfile.objects.create(
            user=user, restaurant=restaurant, role=role, phone=phone
        )
        return staff
