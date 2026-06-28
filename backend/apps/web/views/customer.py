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
    """Customer may edit if they placed this order (tracked in session), it's unpaid, and still pending."""
    if order.is_paid:
        return False
    if order.status != Order.PENDING:
        return False
    customer_orders = request.session.get('customer_orders', [])
    return order.id in customer_orders


def menu(request, table_id):
    table = get_object_or_404(Table, id=table_id, is_active=True)

    # ── QR-only access gate ────────────────────────────────────────────────
    session_key = f'qr_table_{table_id}'
    qr_token = request.GET.get('t', '')
    expected_token = Table.qr_access_token(table_id)

    if qr_token == expected_token:
        # Valid QR scan — grant access for this browser session
        request.session[session_key] = True
        request.session.modified = True
    elif not request.session.get(session_key):
        # No valid token and no prior session — block
        return render(request, 'customer/qr_required.html', {'table': table})
    # ── End gate ──────────────────────────────────────────────────────────

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

    edit_mode = request.GET.get('edit') == '1'
    active_order = None
    active_order_items_json = '[]'
    active_order_id = None
    active_order_customer_name = ''
    active_order_special_instructions = ''

    customer_orders = request.session.get('customer_orders', [])
    if customer_orders:
        active_order = Order.objects.filter(
            id__in=customer_orders,
            table=table,
            is_paid=False
        ).first()

    if active_order and edit_mode:
        active_order_id = active_order.id
        active_order_customer_name = active_order.customer_name
        active_order_special_instructions = active_order.special_instructions
        items_list = []
        for order_item in active_order.items.select_related('menu_item'):
            mi = order_item.menu_item
            if mi:
                image_url = None
                if mi.image:
                    image_url = request.build_absolute_uri(mi.image.url)
                items_list.append({
                    'id': mi.id,
                    'name': mi.name,
                    'description': mi.description,
                    'price': str(mi.price),
                    'food_type': mi.food_type,
                    'is_popular': mi.is_popular,
                    'is_special': mi.is_special,
                    'preparation_time': mi.preparation_time,
                    'calories': mi.calories,
                    'image_url': image_url,
                    'quantity': order_item.quantity,
                    'special_instructions': order_item.special_instructions,
                })
        active_order_items_json = json.dumps(items_list)

    from apps.orders.models import ChargeMaster
    active_charges = ChargeMaster.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).order_by('sequence', 'name')
    
    active_charges_data = []
    for c in active_charges:
        active_charges_data.append({
            'name': c.name,
            'charge_type': c.charge_type,
            'amount': str(c.amount),
            'sequence': c.sequence
        })
    active_charges_json = json.dumps(active_charges_data)

    return render(request, 'customer/menu.html', {
        'table': table,
        'restaurant': restaurant,
        'categories': categories,
        'popular_items': popular_items,
        'special_items': special_items,
        'offers': offers,
        'popular_json': json.dumps([_item_to_dict(i, request) for i in popular_items]),
        'special_json': json.dumps([_item_to_dict(i, request) for i in special_items]),
        'is_edit_mode': edit_mode,
        'active_order_id': active_order_id,
        'active_order_items_json': active_order_items_json,
        'active_order_customer_name': active_order_customer_name,
        'active_order_special_instructions': active_order_special_instructions,
        'active_charges_json': active_charges_json,
    })


@require_GET
def get_category_items(request, table_id, category_id):
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

    active_order_id = body.get('active_order_id')
    is_edit = False
    is_append = False
    order = None

    if active_order_id:
        order = get_object_or_404(Order, id=active_order_id)
        if not _customer_can_edit(request, order):
            return JsonResponse({'error': 'You cannot edit this order.'}, status=403)
        is_edit = True
    else:
        # Check if there is an active unpaid, non-terminal order for this table
        table_active_order = Order.objects.filter(
            table=table,
            is_paid=False
        ).exclude(status__in=[Order.CANCELLED, Order.SERVED]).first()
        
        if table_active_order:
            order = table_active_order
            is_append = True

    if is_edit:
        # Update existing order details and clear old items
        order.special_instructions = body.get('special_instructions', '')
        order.customer_name = body.get('customer_name', '')
        order.save(update_fields=['special_instructions', 'customer_name'])
        order.items.all().delete()
    elif is_append:
        # Append new instructions to existing ones if provided
        new_instructions = body.get('special_instructions', '').strip()
        if new_instructions:
            if order.special_instructions:
                order.special_instructions = f"{order.special_instructions} | {new_instructions}"
            else:
                order.special_instructions = new_instructions
        
        new_name = body.get('customer_name', '').strip()
        if new_name:
            order.customer_name = new_name
            
        # Reset status back to pending since new items require kitchen action
        order.status = Order.PENDING
        order.save(update_fields=['special_instructions', 'customer_name', 'status'])
    else:
        # Create a new order
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
            menu_item = MenuItem.objects.get(id=item_data['menu_item_id'], is_available=True)
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

    # Calculate subtotal, apply dynamic ChargeMaster charges, and set the grand total_amount
    order.calculate_total()

    if is_edit:
        # Log update and notify staff
        OrderLog.objects.create(
            order=order, action='edited', actor_type='customer',
            actor_name=body.get('customer_name', '') or 'Customer',
            details='Updated items: ' + ', '.join(item_names),
        )
        try:
            from apps.orders.utils import send_notification
            from apps.orders.models import Notification
            table_num = order.table.table_number if order.table else 'N/A'
            send_notification(
                restaurant=order.restaurant,
                order=order,
                recipient_type=Notification.STAFF,
                title="Order Updated by Customer",
                message=f"Order #{order.order_number} for Table {table_num} was updated."
            )
        except Exception:
            pass
    elif is_append:
        # Create status history, order log and notify staff for the new round of items
        OrderStatusHistory.objects.create(order=order, status=Order.PENDING)
        OrderLog.objects.create(
            order=order, action='item_added', actor_type='customer',
            actor_name=body.get('customer_name', '') or 'Customer',
            details='Added new items: ' + ', '.join(item_names),
        )
        try:
            from apps.orders.utils import send_notification
            from apps.orders.models import Notification
            table_num = order.table.table_number if order.table else 'N/A'
            send_notification(
                restaurant=order.restaurant,
                order=order,
                recipient_type=Notification.STAFF,
                title="New Items Added to Order",
                message=f"New items were added to Order #{order.order_number} for Table {table_num}."
            )
        except Exception:
            pass
        
        # Ensure order ID is in session so the customer retains edit capability
        customer_orders = request.session.get('customer_orders', [])
        if order.id not in customer_orders:
            customer_orders.append(order.id)
            request.session['customer_orders'] = customer_orders
            request.session.modified = True
    else:
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
        'status': order.status,
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    can_edit = _customer_can_edit(request, order)
    is_edit = order.logs.filter(action='edited').exists()
    return render(request, 'customer/order_success.html', {
        'order': order,
        'can_edit': can_edit,
        'is_edit': is_edit,
    })


def track_order(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item', 'status_history'),
        id=order_id
    )
    steps = [
        ('pending',   'Received', '📋'),
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
