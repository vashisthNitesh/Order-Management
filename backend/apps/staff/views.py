from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import StaffProfile
from .serializers import StaffProfileSerializer, StaffCreateSerializer


class StaffViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.select_related('user', 'restaurant')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'role', 'is_active']

    def get_serializer_class(self):
        if self.action == 'create':
            return StaffCreateSerializer
        return StaffProfileSerializer

    def create(self, request, *args, **kwargs):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = serializer.save()
        return Response(StaffProfileSerializer(staff).data, status=status.HTTP_201_CREATED)
