import io, base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from apps.restaurants.models import Restaurant, Table
from apps.menu.models import Category, MenuItem
from apps.orders.models import Order, OrderItem, OrderStatusHistory, OrderLog
from apps.staff.models import StaffProfile
from apps.offers.models import Offer
from apps.web.decorators import admin_required

RESTAURANT_ID = 1


def _get_restaurant(request):
    try:
        return request.user.staff_profile.restaurant
    except Exception:
        return Restaurant.objects.first()


# ── Auth ─────────────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('web:admin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            is_admin = user.is_superuser
            if not is_admin:
                try:
                    is_admin = user.staff_profile.role in ('admin', 'manager')
                except Exception:
                    pass
            if is_admin:
                login(request, user)
                return redirect('web:admin_dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'admin_panel/login.html')


def admin_logout(request):
    logout(request)
    return redirect('web:admin_login')


# ── Dashboard ─────────────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    restaurant = _get_restaurant(request)
    period = request.GET.get('period', 'today')
    now = timezone.now()
    qs = Order.objects.filter(restaurant=restaurant)
    
    # Calculate stats based on period
    if period == 'yesterday':
        start_date = (now - timedelta(days=1)).date()
        period_qs = qs.filter(created_at__date=start_date)
        period_label = "Yesterday"
    elif period == '7days':
        start_date = (now - timedelta(days=6)).date()
        period_qs = qs.filter(created_at__date__gte=start_date)
        period_label = "Last 7 Days"
    elif period == '30days':
        start_date = (now - timedelta(days=29)).date()
        period_qs = qs.filter(created_at__date__gte=start_date)
        period_label = "Last 30 Days"
    elif period == 'this_month':
        start_date = now.date().replace(day=1)
        period_qs = qs.filter(created_at__date__gte=start_date)
        period_label = "This Month"
    elif period == 'all':
        period_qs = qs
        period_label = "All Time"
    else:  # today
        period = 'today'
        period_qs = qs.filter(created_at__date=now.date())
        period_label = "Today"

    from django.db.models import Sum
    total_orders = period_qs.count()
    total_revenue = period_qs.exclude(status='cancelled').aggregate(t=Sum('total_amount'))['t'] or 0
    active_tables = qs.filter(is_paid=False).exclude(status='cancelled').values('table').distinct().count()
    aov = total_revenue / total_orders if total_orders > 0 else 0

    stats = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending': qs.filter(status='pending').count(),
        'preparing': qs.filter(status='preparing').count(),
        'ready': qs.filter(status='ready').count(),
        'total': qs.count(),
    }
    recent_orders = qs.select_related('table').prefetch_related('items').order_by('-created_at')[:10]
    from django.urls import reverse
    
    rev_fmt = f"₹{int(total_revenue):,}" if total_revenue == int(total_revenue) else f"₹{total_revenue:,.2f}"
    aov_fmt = f"₹{int(aov):,}" if aov == int(aov) else f"₹{aov:,.2f}"

    stats_cards = [
        ('💰', f"Revenue ({period_label})", rev_fmt,      'bg-emerald-50 text-emerald-700', reverse('web:admin_orders') + '?paid=1'),
        ('📦', f"Orders ({period_label})",  total_orders, 'bg-blue-50 text-blue-700',    reverse('web:admin_orders')),
        ('🪑', "Active Tables",            active_tables, 'bg-amber-50 text-amber-700',   reverse('web:admin_orders')),
        ('📊', f"Avg Order Value ({period_label})", aov_fmt, 'bg-indigo-50 text-indigo-700',  reverse('web:admin_orders')),
    ]
    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'stats_cards': stats_cards,
        'recent_orders': recent_orders,
        'restaurant': restaurant,
        'period': period,
        'period_label': period_label,
    })


# ── Tables ────────────────────────────────────────────────────────────────

@admin_required
def admin_tables(request):
    restaurant = _get_restaurant(request)
    tables = Table.objects.filter(restaurant=restaurant).order_by('table_number')
    return render(request, 'admin_panel/tables.html', {
        'tables': tables, 'restaurant': restaurant
    })


@admin_required
def admin_table_save(request, table_id=None):
    restaurant = _get_restaurant(request)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant) if table_id else None

    if request.method == 'POST':
        table_number = request.POST.get('table_number', '').strip()
        capacity = request.POST.get('capacity', 4)
        is_active = request.POST.get('is_active') == 'on'

        if not table_number:
            messages.error(request, 'Table number is required.')
            return redirect('web:admin_tables')

        if table:
            table.table_number = table_number
            table.capacity = capacity
            table.is_active = is_active
            table.save()
            messages.success(request, f'Table {table_number} updated.')
        else:
            if Table.objects.filter(restaurant=restaurant, table_number=table_number).exists():
                messages.error(request, f'Table {table_number} already exists.')
                return redirect('web:admin_tables')
            table = Table(restaurant=restaurant, table_number=table_number, capacity=capacity)
            table.save()
            messages.success(request, f'Table {table_number} created with QR code.')

        # Regenerate QR with current domain
        base_url = f"{request.scheme}://{request.get_host()}"
        table.generate_qr_code(base_url)
        table.save(update_fields=['qr_code'])
        return redirect('web:admin_tables')

    return render(request, 'admin_panel/table_form.html', {'table': table})


@admin_required
@require_POST
def admin_table_delete(request, table_id):
    restaurant = _get_restaurant(request)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    num = table.table_number
    table.delete()
    messages.success(request, f'Table {num} deleted.')
    return redirect('web:admin_tables')


@admin_required
def admin_table_qr(request, table_id):
    restaurant = _get_restaurant(request)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    # Regenerate with current domain each time
    base_url = f"{request.scheme}://{request.get_host()}"
    table.generate_qr_code(base_url)
    table.save(update_fields=['qr_code'])
    if table.qr_code:
        try:
            content = table.qr_code.read()
        except Exception:
            try:
                with table.qr_code.open('rb') as f:
                    content = f.read()
            except Exception:
                import requests
                content = requests.get(table.qr_code.url).content
        
        response = HttpResponse(content, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="table-{table.table_number}-qr.png"'
        return response
    messages.error(request, 'QR code could not be generated.')
    return redirect('web:admin_tables')


@admin_required
def admin_tables_regenerate_all(request):
    restaurant = _get_restaurant(request)
    tables = Table.objects.filter(restaurant=restaurant)
    base_url = f"{request.scheme}://{request.get_host()}"
    for table in tables:
        table.generate_qr_code(base_url)
        table.save(update_fields=['qr_code'])
    messages.success(request, f"Successfully regenerated QR codes for all {tables.count()} tables.")
    return redirect('web:admin_tables')


# ── Menu Items ────────────────────────────────────────────────────────────

@admin_required
def admin_menu(request):
    restaurant = _get_restaurant(request)
    items = MenuItem.objects.filter(
        category__restaurant=restaurant
    ).select_related('category').order_by('category__sort_order', 'sort_order', 'name')
    categories = Category.objects.filter(restaurant=restaurant, is_active=True)
    cat_filter = request.GET.get('category', '')
    search = request.GET.get('search', '')
    if cat_filter:
        items = items.filter(category_id=cat_filter)
    if search:
        items = items.filter(name__icontains=search)
    return render(request, 'admin_panel/menu.html', {
        'items': items, 'categories': categories,
        'cat_filter': cat_filter, 'search': search,
    })


@admin_required
def admin_menu_save(request, item_id=None):
    restaurant = _get_restaurant(request)
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant) if item_id else None
    categories = Category.objects.filter(restaurant=restaurant, is_active=True)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price_str = request.POST.get('price', '').strip()
        category_id = request.POST.get('category', '').strip()
        food_type = request.POST.get('food_type', 'veg')
        is_available = request.POST.get('is_available') == 'on'
        is_popular = request.POST.get('is_popular') == 'on'
        is_special = request.POST.get('is_special') == 'on'
        prep_time = request.POST.get('preparation_time', '15') or '15'
        calories = request.POST.get('calories', '').strip()
        image = request.FILES.get('image')

        if not name or not price_str or not category_id:
            messages.error(request, 'Name, price, and category are required.')
            return render(request, 'admin_panel/menu_form.html', {
                'item': item, 'categories': categories,
            })

        try:
            price = Decimal(price_str)
        except InvalidOperation:
            messages.error(request, 'Invalid price value.')
            return render(request, 'admin_panel/menu_form.html', {
                'item': item, 'categories': categories,
            })

        if item:
            item.name = name
            item.description = description
            item.price = price
            item.category_id = category_id
            item.food_type = food_type
            item.is_available = is_available
            item.is_popular = is_popular
            item.is_special = is_special
            item.preparation_time = int(prep_time)
            item.calories = int(calories) if calories else None
            if image:
                item.image = image
            item.save()
            messages.success(request, f'"{name}" updated.')
        else:
            new_item = MenuItem(
                name=name, description=description, price=price,
                category_id=category_id, food_type=food_type,
                is_available=is_available, is_popular=is_popular,
                is_special=is_special, preparation_time=int(prep_time),
                calories=int(calories) if calories else None,
            )
            if image:
                new_item.image = image
            new_item.save()
            messages.success(request, f'"{name}" added.')
        return redirect('web:admin_menu')

    return render(request, 'admin_panel/menu_form.html', {
        'item': item, 'categories': categories,
    })


@admin_required
@require_POST
def admin_menu_delete(request, item_id):
    restaurant = _get_restaurant(request)
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
    name = item.name
    item.delete()
    messages.success(request, f'"{name}" deleted.')
    return redirect('web:admin_menu')


# ── Categories ────────────────────────────────────────────────────────────

@admin_required
def admin_categories(request):
    restaurant = _get_restaurant(request)
    cats = Category.objects.filter(restaurant=restaurant).order_by('sort_order', 'name')
    return render(request, 'admin_panel/categories.html', {
        'categories': cats, 'restaurant': restaurant,
    })


@admin_required
def admin_category_save(request, cat_id=None):
    restaurant = _get_restaurant(request)
    cat = get_object_or_404(Category, id=cat_id, restaurant=restaurant) if cat_id else None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()
        sort_order = request.POST.get('sort_order', '0') or '0'
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, 'admin_panel/category_form.html', {'cat': cat})

        if cat:
            cat.name = name
            cat.description = description
            cat.icon = icon
            cat.sort_order = int(sort_order)
            cat.is_active = is_active
            if image:
                cat.image = image
            cat.save()
            messages.success(request, f'"{name}" updated.')
        else:
            new_cat = Category(
                restaurant=restaurant, name=name, description=description,
                icon=icon, sort_order=int(sort_order), is_active=is_active,
            )
            if image:
                new_cat.image = image
            new_cat.save()
            messages.success(request, f'"{name}" created.')
        return redirect('web:admin_categories')

    return render(request, 'admin_panel/category_form.html', {'cat': cat})


@admin_required
@require_POST
def admin_category_delete(request, cat_id):
    restaurant = _get_restaurant(request)
    cat = get_object_or_404(Category, id=cat_id, restaurant=restaurant)
    name = cat.name
    cat.delete()
    messages.success(request, f'"{name}" deleted.')
    return redirect('web:admin_categories')


# ── Offers ────────────────────────────────────────────────────────────────

@admin_required
def admin_offers(request):
    restaurant = _get_restaurant(request)
    offers = Offer.objects.filter(restaurant=restaurant).order_by('-created_at')
    return render(request, 'admin_panel/offers.html', {'offers': offers})


@admin_required
def admin_offer_save(request, offer_id=None):
    restaurant = _get_restaurant(request)
    offer = get_object_or_404(Offer, id=offer_id, restaurant=restaurant) if offer_id else None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value', '0')
        min_order = request.POST.get('min_order_amount', '0') or '0'
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        promo_code = request.POST.get('promo_code', '').strip()

        if not title:
            messages.error(request, 'Title is required.')
            return render(request, 'admin_panel/offer_form.html', {'offer': offer})

        if offer:
            offer.title = title
            offer.description = description
            offer.discount_type = discount_type
            offer.discount_value = Decimal(discount_value)
            offer.min_order_amount = Decimal(min_order)
            offer.start_date = start_date
            offer.end_date = end_date
            offer.is_active = is_active
            offer.promo_code = promo_code
            offer.save()
            messages.success(request, f'Offer "{title}" updated.')
        else:
            Offer.objects.create(
                restaurant=restaurant, title=title, description=description,
                discount_type=discount_type, discount_value=Decimal(discount_value),
                min_order_amount=Decimal(min_order), start_date=start_date,
                end_date=end_date, is_active=is_active, promo_code=promo_code,
            )
            messages.success(request, f'Offer "{title}" created.')
        return redirect('web:admin_offers')

    return render(request, 'admin_panel/offer_form.html', {'offer': offer})


@admin_required
@require_POST
def admin_offer_delete(request, offer_id):
    restaurant = _get_restaurant(request)
    offer = get_object_or_404(Offer, id=offer_id, restaurant=restaurant)
    title = offer.title
    offer.delete()
    messages.success(request, f'Offer "{title}" deleted.')
    return redirect('web:admin_offers')


# ── Staff Management ──────────────────────────────────────────────────────

@admin_required
def admin_staff(request):
    restaurant = _get_restaurant(request)
    staff_list = StaffProfile.objects.filter(
        restaurant=restaurant
    ).select_related('user').order_by('user__first_name')
    return render(request, 'admin_panel/staff.html', {'staff_list': staff_list})


@admin_required
def admin_staff_save(request, staff_id=None):
    restaurant = _get_restaurant(request)
    staff = get_object_or_404(StaffProfile, id=staff_id, restaurant=restaurant) if staff_id else None

    if request.method == 'POST':
        if staff:
            # Edit existing
            staff.role = request.POST.get('role', staff.role)
            staff.phone = request.POST.get('phone', '').strip()
            staff.is_active = request.POST.get('is_active') == 'on'
            staff.user.first_name = request.POST.get('first_name', '').strip()
            staff.user.last_name = request.POST.get('last_name', '').strip()
            staff.user.email = request.POST.get('email', '').strip()
            staff.user.save()
            staff.save()
            messages.success(request, f'Staff "{staff.user.get_full_name()}" updated.')
        else:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            role = request.POST.get('role', 'waiter')
            phone = request.POST.get('phone', '').strip()

            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists.')
                return render(request, 'admin_panel/staff_form.html', {'staff': None})

            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name,
            )
            StaffProfile.objects.create(
                user=user, restaurant=restaurant, role=role, phone=phone,
            )
            messages.success(request, f'Staff account for "{first_name}" created.')
        return redirect('web:admin_staff')

    return render(request, 'admin_panel/staff_form.html', {'staff': staff})


@admin_required
@require_POST
def admin_staff_delete(request, staff_id):
    restaurant = _get_restaurant(request)
    staff = get_object_or_404(StaffProfile, id=staff_id, restaurant=restaurant)
    name = staff.user.get_full_name() or staff.user.username
    staff.user.delete()
    messages.success(request, f'Staff "{name}" removed.')
    return redirect('web:admin_staff')


# ── Orders / Invoices ─────────────────────────────────────────────────────

def _actor_name(user):
    return user.get_full_name() or user.username


@admin_required
def admin_orders(request):
    restaurant = _get_restaurant(request)
    qs = Order.objects.filter(restaurant=restaurant).select_related('table').prefetch_related('items').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    paid_filter = request.GET.get('paid', '')
    search = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if paid_filter == '1':
        qs = qs.filter(is_paid=True)
    elif paid_filter == '0':
        qs = qs.filter(is_paid=False)
    if search:
        qs = qs.filter(order_number__icontains=search)

    return render(request, 'admin_panel/orders.html', {
        'orders': qs[:150],
        'status_filter': status_filter,
        'paid_filter': paid_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    })


@admin_required
def admin_order_detail(request, order_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__menu_item__category',
            'logs',
            'status_history__changed_by',
        ).select_related('table', 'paid_by'),
        id=order_id, restaurant=restaurant,
    )
    menu_items = MenuItem.objects.filter(
        category__restaurant=restaurant, is_available=True
    ).select_related('category').order_by('category__name', 'name')

    # Status timestamps mapping
    history_map = {h.status: h.created_at for h in order.status_history.all()}
    if 'pending' not in history_map:
        history_map['pending'] = order.created_at

    status_sequence = ['pending', 'confirmed', 'preparing', 'ready', 'served']
    next_status = None
    if order.status in status_sequence:
        current_idx = status_sequence.index(order.status)
        if current_idx < len(status_sequence) - 1:
            next_status = status_sequence[current_idx + 1]

    return render(request, 'admin_panel/order_detail.html', {
        'order': order,
        'menu_items': menu_items,
        'history_map': history_map,
        'next_status': next_status,
        'status_sequence': status_sequence,
    })


@admin_required
@require_POST
def admin_order_item_update(request, order_id, item_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    if order.is_paid:
        messages.error(request, 'Cannot edit a paid invoice.')
        return redirect('web:admin_order_detail', order_id=order_id)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1
    if qty <= 0:
        name = item.menu_item.name if item.menu_item else 'Item'
        item.delete()
        order.calculate_total()
        OrderLog.objects.create(order=order, action='item_removed', actor_type='staff',
                                actor_name=_actor_name(request.user), details=f'Removed {name}')
        messages.success(request, f'"{name}" removed.')
    else:
        old_qty = item.quantity
        item.quantity = qty
        item.save(update_fields=['quantity'])
        order.calculate_total()
        name = item.menu_item.name if item.menu_item else 'Item'
        OrderLog.objects.create(order=order, action='qty_changed', actor_type='staff',
                                actor_name=_actor_name(request.user),
                                details=f'{name}: {old_qty} → {qty}')
        messages.success(request, 'Quantity updated.')
    return redirect('web:admin_order_detail', order_id=order_id)


@admin_required
@require_POST
def admin_order_item_delete(request, order_id, item_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    if order.is_paid:
        messages.error(request, 'Cannot edit a paid invoice.')
        return redirect('web:admin_order_detail', order_id=order_id)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    name = item.menu_item.name if item.menu_item else 'Item'
    item.delete()
    order.calculate_total()
    OrderLog.objects.create(order=order, action='item_removed', actor_type='staff',
                            actor_name=_actor_name(request.user), details=f'Removed {name}')
    messages.success(request, f'"{name}" removed from order.')
    return redirect('web:admin_order_detail', order_id=order_id)


@admin_required
@require_POST
def admin_order_item_add(request, order_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    if order.is_paid:
        messages.error(request, 'Cannot edit a paid invoice.')
        return redirect('web:admin_order_detail', order_id=order_id)
    menu_item_id = request.POST.get('menu_item_id', '').strip()
    try:
        qty = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        qty = 1
    try:
        menu_item = MenuItem.objects.get(id=menu_item_id, category__restaurant=restaurant)
    except MenuItem.DoesNotExist:
        messages.error(request, 'Item not found.')
        return redirect('web:admin_order_detail', order_id=order_id)

    existing = order.items.filter(menu_item=menu_item).first()
    if existing:
        existing.quantity += qty
        existing.save(update_fields=['quantity'])
        detail = f'{menu_item.name}: qty now {existing.quantity}'
    else:
        OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty, unit_price=menu_item.price)
        detail = f'Added {menu_item.name} ×{qty}'

    order.calculate_total()
    OrderLog.objects.create(order=order, action='item_added', actor_type='staff',
                            actor_name=_actor_name(request.user), details=detail)
    messages.success(request, f'"{menu_item.name}" added.')
    return redirect('web:admin_order_detail', order_id=order_id)


@admin_required
@require_POST
def admin_order_mark_paid(request, order_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    if order.is_paid:
        messages.info(request, 'Order is already marked as paid.')
        return redirect('web:admin_order_detail', order_id=order_id)
    order.is_paid = True
    order.paid_at = timezone.now()
    order.paid_by = request.user
    if order.status not in (Order.SERVED, Order.CANCELLED):
        order.status = Order.SERVED
    order.save(update_fields=['is_paid', 'paid_at', 'paid_by', 'status'])
    OrderStatusHistory.objects.create(order=order, status=Order.SERVED, changed_by=request.user, note='Marked as paid')
    OrderLog.objects.create(order=order, action='paid', actor_type='staff',
                            actor_name=_actor_name(request.user),
                            details=f'Invoice marked as paid. Total: {order.total_amount}')
    messages.success(request, f'Order #{order.order_number} marked as paid.')
    return redirect('web:admin_order_detail', order_id=order_id)


@admin_required
@require_POST
def admin_order_update_note(request, order_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    if order.is_paid:
        messages.error(request, 'Cannot edit a paid invoice.')
        return redirect('web:admin_order_detail', order_id=order_id)
    order.special_instructions = request.POST.get('special_instructions', '').strip()
    order.save(update_fields=['special_instructions'])
    OrderLog.objects.create(order=order, action='note_updated', actor_type='staff',
                            actor_name=_actor_name(request.user), details='Special instructions updated')
    messages.success(request, 'Note updated.')
    return redirect('web:admin_order_detail', order_id=order_id)


@admin_required
@require_POST
def admin_order_status_update(request, order_id):
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    new_status = request.POST.get('status')
    if new_status not in dict(Order.STATUS_CHOICES):
        messages.error(request, 'Invalid status.')
        return redirect('web:admin_order_detail', order_id=order_id)
    old_status = order.status
    order.status = new_status
    order.save(update_fields=['status'])
    OrderStatusHistory.objects.create(order=order, status=new_status, changed_by=request.user)
    OrderLog.objects.create(order=order, action='status_changed', actor_type='staff',
                            actor_name=_actor_name(request.user),
                            details=f'{old_status} → {new_status}')
    messages.success(request, f'Status updated to {new_status}.')
    return redirect('web:admin_order_detail', order_id=order_id)


@admin_required
@require_POST
def admin_order_item_toggle_available(request, order_id, item_id):
    """Mark the underlying menu item unavailable directly from an invoice."""
    restaurant = _get_restaurant(request)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    if item.menu_item:
        item.menu_item.is_available = False
        item.menu_item.save(update_fields=['is_available'])
        messages.success(request, f'"{item.menu_item.name}" marked unavailable on the menu.')
    return redirect('web:admin_order_detail', order_id=order_id)


# ── Logs ──────────────────────────────────────────────────────────────────

@admin_required
def admin_logs(request):
    restaurant = _get_restaurant(request)
    logs = OrderLog.objects.filter(
        order__restaurant=restaurant
    ).select_related('order__table').order_by('-created_at')

    order_q = request.GET.get('order', '')
    action_filter = request.GET.get('action', '')
    actor_filter = request.GET.get('actor', '')

    if order_q:
        logs = logs.filter(order__order_number__icontains=order_q)
    if action_filter:
        logs = logs.filter(action=action_filter)
    if actor_filter:
        logs = logs.filter(actor_type=actor_filter)

    return render(request, 'admin_panel/logs.html', {
        'logs': logs[:300],
        'order_q': order_q,
        'action_filter': action_filter,
        'actor_filter': actor_filter,
        'action_choices': OrderLog.ACTION_CHOICES,
    })
