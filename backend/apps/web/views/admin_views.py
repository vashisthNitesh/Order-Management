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
from apps.orders.models import Order
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
    today = timezone.now().date()
    qs = Order.objects.filter(restaurant=restaurant)
    today_qs = qs.filter(created_at__date=today)

    from django.db.models import Sum
    stats = {
        'today_orders': today_qs.count(),
        'today_revenue': today_qs.exclude(status='cancelled').aggregate(t=Sum('total_amount'))['t'] or 0,
        'pending': qs.filter(status='pending').count(),
        'preparing': qs.filter(status='preparing').count(),
        'ready': qs.filter(status='ready').count(),
        'total': qs.count(),
    }
    recent_orders = qs.select_related('table').prefetch_related('items').order_by('-created_at')[:10]
    rev = stats['today_revenue']
    rev_fmt = f"₹{int(rev):,}" if rev == int(rev) else f"₹{rev:,.2f}"
    stats_cards = [
        ('📦', "Today's Orders", stats['today_orders'], 'bg-blue-100'),
        ('💰', "Today's Revenue", rev_fmt, 'bg-emerald-100'),
        ('⏳', 'Pending', stats['pending'], 'bg-yellow-100'),
        ('🍳', 'Preparing', stats['preparing'], 'bg-orange-100'),
    ]
    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'stats_cards': stats_cards,
        'recent_orders': recent_orders,
        'restaurant': restaurant,
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
        with open(table.qr_code.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="table-{table.table_number}-qr.png"'
            return response
    messages.error(request, 'QR code could not be generated.')
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
