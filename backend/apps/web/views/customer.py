import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone

from apps.restaurants.models import Restaurant, Table
from apps.menu.models import Category, MenuItem
from apps.orders.models import Order, OrderItem, OrderStatusHistory, OrderLog
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


def _customer_can_edit(request, order):
    """Customer may edit if they placed this order (tracked in session) and it's unpaid."""
    if order.is_paid:
        return False
    customer_orders = request.session.get('customer_orders', [])
    return order.id in customer_orders


def menu(request, table_id):
    table = get_object_or_404(Table, id=table_id, is_active=True)
    restaurant = table.restaurant

    from django.db.models import Count, Q
    categories = Category.objects.filter(
        restaurant=restaurant, is_active=True
    ).annotate(
        item_count=Count('items', filter=Q(items__is_available=True))
    ).filter(item_count__gt=0).order_by('sort_order', 'name')

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
        'categories': categories,
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
    item_names = []
    for item_data in items_data:
        try:
            menu_item = MenuItem.objects.get(id=item_data['menu_item_id'])
        except MenuItem.DoesNotExist:
            continue
        qty = int(item_data.get('quantity', 1))
        unit_price = menu_item.price
        total += unit_price * qty
        item_names.append(f'{menu_item.name} ×{qty}')
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
    OrderLog.objects.create(
        order=order, action='created', actor_type='customer',
        actor_name=body.get('customer_name', '') or 'Customer',
        details=', '.join(item_names),
    )

    # Store order in session so customer can edit it later
    customer_orders = request.session.get('customer_orders', [])
    if order.id not in customer_orders:
        customer_orders.append(order.id)
        request.session['customer_orders'] = customer_orders
        request.session.modified = True

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'order_number': order.order_number,
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    can_edit = _customer_can_edit(request, order)
    return render(request, 'customer/order_success.html', {
        'order': order,
        'can_edit': can_edit,
    })


def track_order(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item', 'status_history'),
        id=order_id
    )
    steps = [
        ('pending',   'Order Received', '📋'),
        ('confirmed', 'Confirmed',       '✅'),
        ('preparing', 'Preparing',       '👨‍🍳'),
        ('ready',     'Ready',           '🔔'),
        ('served',    'Served',          '🍽️'),
    ]
    current_index = next(
        (i for i, (s, _, _) in enumerate(steps) if s == order.status), -1
    )
    can_edit = _customer_can_edit(request, order)
    return render(request, 'customer/tracking.html', {
        'order': order,
        'steps': steps,
        'current_index': current_index,
        'can_edit': can_edit,
    })


def customer_order_edit(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item__category'),
        order_number=order_number,
    )
    can_edit = _customer_can_edit(request, order)
    menu_items = []
    if can_edit:
        menu_items = MenuItem.objects.filter(
            category__restaurant=order.restaurant,
            is_available=True,
        ).select_related('category').order_by('category__name', 'name')
    return render(request, 'customer/order_edit.html', {
        'order': order,
        'can_edit': can_edit,
        'menu_items': menu_items,
    })


@require_POST
def customer_item_update(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _customer_can_edit(request, order):
        messages.error(request, 'You cannot edit this order.')
        return redirect('web:track_order', order_id=order.id)

    item_id = request.POST.get('item_id')
    try:
        qty = int(request.POST.get('quantity', 0))
    except (ValueError, TypeError):
        qty = 0

    item = get_object_or_404(OrderItem, id=item_id, order=order)
    name = item.menu_item.name if item.menu_item else 'Item'

    if qty <= 0:
        item.delete()
        order.calculate_total()
        OrderLog.objects.create(order=order, action='item_removed', actor_type='customer',
                                actor_name=order.customer_name or 'Customer',
                                details=f'Removed {name}')
        messages.success(request, f'"{name}" removed.')
    else:
        old_qty = item.quantity
        item.quantity = qty
        item.save(update_fields=['quantity'])
        order.calculate_total()
        OrderLog.objects.create(order=order, action='qty_changed', actor_type='customer',
                                actor_name=order.customer_name or 'Customer',
                                details=f'{name}: {old_qty} → {qty}')
        messages.success(request, 'Quantity updated.')

    return redirect('web:customer_order_edit', order_number=order_number)


@require_POST
def customer_item_add(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _customer_can_edit(request, order):
        messages.error(request, 'You cannot edit this order.')
        return redirect('web:track_order', order_id=order.id)

    menu_item_id = request.POST.get('menu_item_id', '').strip()
    try:
        qty = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        qty = 1

    try:
        menu_item = MenuItem.objects.get(id=menu_item_id, is_available=True,
                                         category__restaurant=order.restaurant)
    except MenuItem.DoesNotExist:
        messages.error(request, 'Item not available.')
        return redirect('web:customer_order_edit', order_number=order_number)

    existing = order.items.filter(menu_item=menu_item).first()
    if existing:
        existing.quantity += qty
        existing.save(update_fields=['quantity'])
        detail = f'{menu_item.name}: qty now {existing.quantity}'
    else:
        OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty, unit_price=menu_item.price)
        detail = f'Added {menu_item.name} ×{qty}'

    order.calculate_total()
    OrderLog.objects.create(order=order, action='item_added', actor_type='customer',
                            actor_name=order.customer_name or 'Customer', details=detail)
    messages.success(request, f'"{menu_item.name}" added.')
    return redirect('web:customer_order_edit', order_number=order_number)


@require_POST
def customer_update_note(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _customer_can_edit(request, order):
        messages.error(request, 'You cannot edit this order.')
        return redirect('web:track_order', order_id=order.id)
    order.special_instructions = request.POST.get('special_instructions', '').strip()
    order.save(update_fields=['special_instructions'])
    OrderLog.objects.create(order=order, action='note_updated', actor_type='customer',
                            actor_name=order.customer_name or 'Customer',
                            details='Special instructions updated')
    messages.success(request, 'Note updated.')
    return redirect('web:customer_order_edit', order_number=order_number)
