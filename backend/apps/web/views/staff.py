from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from apps.orders.models import Order, OrderStatusHistory
from apps.web.decorators import staff_required


def staff_login(request):
    if request.user.is_authenticated:
        return redirect('web:staff_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            login(request, user)
            if user.is_superuser or getattr(getattr(user, 'staff_profile', None), 'role', None) in ('admin', 'manager'):
                return redirect('web:admin_dashboard')
            return redirect('web:staff_dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'staff/login.html')


def staff_logout(request):
    logout(request)
    return redirect('web:staff_login')


@staff_required
def staff_dashboard(request):
    status_filter = request.GET.get('status', '')
    qs = Order.objects.select_related('table').prefetch_related('items__menu_item')
    try:
        restaurant = request.user.staff_profile.restaurant
        qs = qs.filter(restaurant=restaurant)
    except Exception:
        pass

    if status_filter:
        qs = qs.filter(status=status_filter)
    else:
        qs = qs.exclude(status__in=['served', 'cancelled'])

    orders = qs.order_by('-created_at')[:50]

    status_counts = {}
    base_qs = Order.objects.all()
    try:
        base_qs = base_qs.filter(restaurant=request.user.staff_profile.restaurant)
    except Exception:
        pass
    for s in ['pending', 'confirmed', 'preparing', 'ready']:
        status_counts[s] = base_qs.filter(status=s).count()

    status_tabs = [
        ('', 'All Active', 'bg-gray-100 text-gray-700'),
        ('pending', 'New', 'bg-yellow-100 text-yellow-700'),
        ('confirmed', 'Confirmed', 'bg-blue-100 text-blue-700'),
        ('preparing', 'Cooking', 'bg-orange-100 text-orange-700'),
        ('ready', 'Ready', 'bg-green-100 text-green-700'),
        ('served', 'Served', 'bg-gray-100 text-gray-500'),
    ]
    return render(request, 'staff/dashboard.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'status_tabs': status_tabs,
    })


@staff_required
def staff_kitchen(request):
    qs = Order.objects.select_related('table').prefetch_related('items__menu_item')
    try:
        qs = qs.filter(restaurant=request.user.staff_profile.restaurant)
    except Exception:
        pass

    # "New Orders" shows both pending and confirmed — confirmed means front-of-house
    # acknowledged the order; kitchen still needs to start cooking it.
    queued_orders = qs.filter(status__in=['pending', 'confirmed']).order_by('created_at')
    preparing_orders = qs.filter(status='preparing').order_by('created_at')
    ready_orders = qs.filter(status='ready').order_by('created_at')

    return render(request, 'staff/kitchen.html', {
        'pending_orders': queued_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
    })


@staff_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status') or request.GET.get('status')
    valid = dict(Order.STATUS_CHOICES).keys()
    if new_status not in valid:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    OrderStatusHistory.objects.create(order=order, status=new_status, changed_by=request.user)
    order.status = new_status
    order.save(update_fields=['status'])
    # Return to the page that called us
    referer = request.META.get('HTTP_REFERER', '')
    if 'kitchen' in referer:
        return redirect('web:staff_kitchen')
    return redirect('web:staff_dashboard')


@staff_required
@require_POST
def staff_order_mark_paid(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.is_paid:
        messages.info(request, 'Order is already marked as paid.')
        return redirect('web:staff_dashboard')
        
    old_status = order.status
    order.is_paid = True
    from django.utils import timezone
    order.paid_at = timezone.now()
    order.paid_by = request.user
    if order.status not in (Order.SERVED, Order.CANCELLED):
        order.status = Order.SERVED
    order.save(update_fields=['is_paid', 'paid_at', 'paid_by', 'status'])

    # Only log a status change if the status actually moved
    if old_status != order.status:
        OrderStatusHistory.objects.create(order=order, status=order.status, changed_by=request.user, note='Marked as paid by staff')
    
    from apps.orders.models import OrderLog
    actor_name = request.user.get_full_name() or request.user.username
    OrderLog.objects.create(
        order=order,
        action='paid',
        actor_type='staff',
        actor_name=actor_name,
        details=f'Invoice marked as paid via Staff Portal. Total: {order.total_amount}'
    )
    
    messages.success(request, f'Order #{order.order_number} marked as paid successfully.')
    return redirect('web:staff_dashboard')


@staff_required
def staff_kitchen_api(request):
    from django.db.models import Count
    qs = Order.objects.all()
    try:
        qs = qs.filter(restaurant=request.user.staff_profile.restaurant)
    except Exception:
        pass
    counts = dict(
        qs.filter(status__in=['pending', 'confirmed', 'preparing', 'ready'])
          .values('status')
          .annotate(c=Count('id'))
          .values_list('status', 'c')
    )
    return JsonResponse({
        'queued': counts.get('pending', 0) + counts.get('confirmed', 0),
        'preparing': counts.get('preparing', 0),
        'ready': counts.get('ready', 0),
    })
