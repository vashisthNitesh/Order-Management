import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from apps.restaurants.models import Restaurant, Table
from apps.menu.models import Category, MenuItem
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.offers.models import Offer


def _item_to_dict(item, request=None):
    image_url = None
    if item.image:
        image_url = request.build_absolute_uri(item.image.url) if request else item.image.url
    return {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'price': str(item.price),
        'food_type': item.food_type,
        'is_popular': item.is_popular,
        'is_special': item.is_special,
        'preparation_time': item.preparation_time,
        'calories': item.calories,
        'image_url': image_url,
    }


def menu(request, table_id):
    table = get_object_or_404(Table, id=table_id, is_active=True)
    restaurant = table.restaurant

    categories = Category.objects.filter(
        restaurant=restaurant, is_active=True
    ).prefetch_related('items').order_by('sort_order', 'name')

    # Only categories that have available items
    categories_with_items = [
        c for c in categories if c.items.filter(is_available=True).exists()
    ]

    popular_items = MenuItem.objects.filter(
        category__restaurant=restaurant,
        is_popular=True,
        is_available=True
    ).select_related('category')[:12]

    special_items = MenuItem.objects.filter(
        category__restaurant=restaurant,
        is_special=True,
        is_available=True
    ).select_related('category')[:8]

    now = timezone.now()
    offers = Offer.objects.filter(
        restaurant=restaurant,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
    )

    return render(request, 'customer/menu.html', {
        'table': table,
        'restaurant': restaurant,
        'categories': categories_with_items,
        'popular_items': popular_items,
        'special_items': special_items,
        'offers': offers,
        'popular_json': json.dumps([_item_to_dict(i, request) for i in popular_items]),
        'special_json': json.dumps([_item_to_dict(i, request) for i in special_items]),
    })


@require_GET
def get_category_items(request, category_id):
    items = MenuItem.objects.filter(
        category_id=category_id, is_available=True
    ).select_related('category').order_by('sort_order', 'name')
    return JsonResponse({'items': [_item_to_dict(i, request) for i in items]})


@require_POST
@csrf_exempt
def place_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    items_data = body.get('items', [])
    if not items_data:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    order = Order.objects.create(
        restaurant=table.restaurant,
        table=table,
        special_instructions=body.get('special_instructions', ''),
        customer_name=body.get('customer_name', ''),
        status=Order.PENDING,
    )

    total = 0
    for item_data in items_data:
        try:
            menu_item = MenuItem.objects.get(id=item_data['menu_item_id'])
        except MenuItem.DoesNotExist:
            continue
        qty = int(item_data.get('quantity', 1))
        unit_price = menu_item.price
        subtotal = unit_price * qty
        total += subtotal
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=qty,
            unit_price=unit_price,
            special_instructions=item_data.get('special_instructions', ''),
        )

    order.total_amount = total
    order.save(update_fields=['total_amount'])
    OrderStatusHistory.objects.create(order=order, status=Order.PENDING)

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'order_number': order.order_number,
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'customer/order_success.html', {'order': order})


def track_order(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item', 'status_history'),
        id=order_id
    )
    steps = [
        ('pending', 'Order Received', '📋'),
        ('confirmed', 'Confirmed', '✅'),
        ('preparing', 'Preparing', '👨‍🍳'),
        ('ready', 'Ready', '🔔'),
        ('served', 'Served', '🍽️'),
    ]
    current_index = next(
        (i for i, (s, _, _) in enumerate(steps) if s == order.status), -1
    )
    return render(request, 'customer/tracking.html', {
        'order': order,
        'steps': steps,
        'current_index': current_index,
    })
