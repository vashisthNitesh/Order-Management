import json
from django.utils import timezone
from apps.orders.redis_client import get_redis_client

def send_notification(restaurant, order, recipient_type, title, message):
    """
    Creates a Notification database record and pushes a JSON payload to Redis.
    """
    from apps.orders.models import Notification
    
    # 1. Save to DB for persistence & history
    notification = Notification.objects.create(
        restaurant=restaurant,
        order=order,
        recipient_type=recipient_type,
        title=title,
        message=message
    )

    # 2. Push to Redis if connection is available
    redis_client = get_redis_client()
    if redis_client:
        try:
            payload = {
                'id': notification.id,
                'order_id': order.id if order else None,
                'order_number': order.order_number if order else None,
                'recipient_type': recipient_type,
                'title': title,
                'message': message,
                'created_at': timezone.now().isoformat(),
            }
            payload_str = json.dumps(payload)

            if recipient_type == Notification.STAFF:
                redis_key = f"notifications:restaurant:{restaurant.id}:staff"
            else:
                redis_key = f"notifications:order:{order.id}"

            # LPUSH inserts at the head of the list
            redis_client.lpush(redis_key, payload_str)
            # Keep only the last 50 notifications in memory to prevent leaks
            redis_client.ltrim(redis_key, 0, 49)
        except Exception:
            # Silently fallback if Redis fails during push
            pass

    return notification

def notify_order_change(order, is_new, old_status):
    """
    Helper dispatched from the Order.save() method.
    """
    from apps.orders.models import Notification

    if is_new:
        # Notify staff of a new order
        table_num = order.table.table_number if order.table else 'N/A'
        send_notification(
            restaurant=order.restaurant,
            order=order,
            recipient_type=Notification.STAFF,
            title="New Order Placed",
            message=f"Order #{order.order_number} for Table {table_num} is pending."
        )
    elif old_status != order.status:
        # Notify customer of status change
        send_notification(
            restaurant=order.restaurant,
            order=order,
            recipient_type=Notification.CUSTOMER,
            title="Order Status Updated",
            message=f"Your order #{order.order_number} status is now: {order.status.upper()}."
        )
