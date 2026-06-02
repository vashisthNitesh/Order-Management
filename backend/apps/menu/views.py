from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, MenuItem
from .serializers import CategorySerializer, CategoryListSerializer, MenuItemSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related('restaurant').prefetch_related('items')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['restaurant', 'is_active']
    search_fields = ['name']
    ordering_fields = ['sort_order', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related('category__restaurant')
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'food_type', 'is_popular', 'is_special', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'sort_order', 'name', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def popular(self, request):
        items = self.get_queryset().filter(is_popular=True, is_available=True)
        restaurant_id = request.query_params.get('restaurant')
        if restaurant_id:
            items = items.filter(category__restaurant_id=restaurant_id)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def specials(self, request):
        items = self.get_queryset().filter(is_special=True, is_available=True)
        restaurant_id = request.query_params.get('restaurant')
        if restaurant_id:
            items = items.filter(category__restaurant_id=restaurant_id)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
