from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Offer
from .serializers import OfferSerializer


class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'is_active', 'discount_type']

    def get_queryset(self):
        qs = Offer.objects.prefetch_related('applicable_items', 'applicable_categories')
        if self.request.query_params.get('active_only') == 'true':
            now = timezone.now()
            qs = qs.filter(is_active=True, start_date__lte=now, end_date__gte=now)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
