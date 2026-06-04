from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Restaurant, Table
from .serializers import RestaurantSerializer, TableSerializer, TableCreateSerializer


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.select_related('restaurant').all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'is_active']

    def get_serializer_class(self):
        if self.action == 'create':
            return TableCreateSerializer
        return TableSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def regenerate_qr(self, request, pk=None):
        table = self.get_object()
        base_url = request.data.get('base_url')
        table.generate_qr_code(base_url)
        table.save()
        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)
