from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderItem, Notification
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer,
    OrderStatusHistorySerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'restaurant', 'table']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        return Order.objects.select_related(
            'restaurant', 'table'
        ).prefetch_related(
            'items__menu_item', 'status_history__changed_by'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        from .models import OrderStatusHistory
        OrderStatusHistory.objects.create(order=order, status=new_status, changed_by=request.user)
        order.status = new_status
        order.save(update_fields=['status'])
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def dashboard_stats(self, request):
        restaurant_id = request.query_params.get('restaurant')
        today = timezone.now().date()

        qs = Order.objects.filter(restaurant_id=restaurant_id) if restaurant_id else Order.objects.all()
        today_orders = qs.filter(created_at__date=today)

        stats = {
            'today_orders': today_orders.count(),
            'today_revenue': today_orders.filter(
                status__in=['served', 'ready', 'preparing', 'confirmed']
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            'pending_orders': qs.filter(status='pending').count(),
            'preparing_orders': qs.filter(status='preparing').count(),
            'ready_orders': qs.filter(status='ready').count(),
            'total_orders': qs.count(),
        }
        return Response(stats)


import json
from django.http import JsonResponse
from apps.orders.redis_client import get_redis_client

def notification_poll(request):
    """
    Poll endpoint that retrieves notifications from Redis,
    falling back to database if Redis is empty or down.
    """
    last_seen_id_str = request.GET.get('last_seen_id', '0')
    try:
        last_seen_id = int(last_seen_id_str)
    except ValueError:
        last_seen_id = 0

    order_id = request.GET.get('order_id')
    restaurant_id = request.GET.get('restaurant_id')

    notifications = []
    redis_success = False

    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_key = None
            if order_id:
                redis_key = f"notifications:order:{order_id}"
            elif restaurant_id:
                redis_key = f"notifications:restaurant:{restaurant_id}:staff"

            if redis_key:
                raw_items = redis_client.lrange(redis_key, 0, -1)
                for item_str in raw_items:
                    item = json.loads(item_str)
                    if item.get('id', 0) > last_seen_id:
                        notifications.append(item)
                # Sort ascending by id
                notifications.sort(key=lambda x: x['id'])
                redis_success = True
        except Exception:
            pass

    # Fallback to database
    if not redis_success:
        db_qs = Notification.objects.filter(id__gt=last_seen_id)
        if order_id:
            db_qs = db_qs.filter(order_id=order_id, recipient_type=Notification.CUSTOMER)
        elif restaurant_id:
            db_qs = db_qs.filter(restaurant_id=restaurant_id, recipient_type=Notification.STAFF)
        else:
            db_qs = db_qs.none()

        db_qs = db_qs.order_by('id')
        for n in db_qs:
            notifications.append({
                'id': n.id,
                'order_id': n.order_id,
                'order_number': n.order.order_number if n.order else None,
                'recipient_type': n.recipient_type,
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.isoformat(),
            })

    return JsonResponse({'notifications': notifications})
