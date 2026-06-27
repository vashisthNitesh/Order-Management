from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.restaurants.models import Restaurant
from apps.staff.models import StaffProfile


def org_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('web:org_login')
        return view_func(request, *args, **kwargs)
    return wrapped


def org_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('web:org_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_active and user.is_superuser:
            login(request, user)
            return redirect('web:org_dashboard')
        messages.error(request, 'Invalid credentials or you do not have org-level access.')
    return render(request, 'org/login.html')


def org_logout(request):
    logout(request)
    return redirect('web:org_login')


@org_required
def org_dashboard(request):
    restaurants = Restaurant.objects.prefetch_related('staff', 'tables').order_by('-created_at')
    return render(request, 'org/dashboard.html', {'restaurants': restaurants})


@org_required
def org_restaurant_save(request, restaurant_id=None):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id) if restaurant_id else None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        region = request.POST.get('region', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()

        if not name:
            messages.error(request, 'Restaurant name is required.')
            return render(request, 'org/restaurant_form.html', {'restaurant': restaurant})

        if restaurant:
            restaurant.name = name
            restaurant.region = region
            restaurant.phone = phone
            restaurant.email = email
            if request.FILES.get('logo'):
                restaurant.logo = request.FILES['logo']
            restaurant.save()
            messages.success(request, f'"{name}" updated.')
            return redirect('web:org_dashboard')
        else:
            restaurant = Restaurant(name=name, region=region, phone=phone, email=email)
            if request.FILES.get('logo'):
                restaurant.logo = request.FILES['logo']
            restaurant.save()

            admin_username = request.POST.get('admin_username', '').strip()
            admin_email = request.POST.get('admin_email', '').strip()
            admin_password = request.POST.get('admin_password', '').strip()

            if admin_username and admin_password:
                if User.objects.filter(username=admin_username).exists():
                    messages.warning(request, f'Restaurant created but username "{admin_username}" already exists — pick a different one.')
                else:
                    user = User.objects.create_user(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password,
                        is_staff=True,
                    )
                    StaffProfile.objects.create(user=user, restaurant=restaurant, role='admin')
                    messages.success(request, f'Restaurant "{name}" and admin user "{admin_username}" created.')
            else:
                messages.success(request, f'Restaurant "{name}" created. Add staff from the restaurant admin panel.')

            return redirect('web:org_dashboard')

    return render(request, 'org/restaurant_form.html', {'restaurant': restaurant})


@org_required
@require_POST
def org_restaurant_delete(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    name = restaurant.name
    restaurant.delete()
    messages.success(request, f'"{name}" deleted.')
    return redirect('web:org_dashboard')


@org_required
def org_switch_restaurant(request, restaurant_id):
    get_object_or_404(Restaurant, id=restaurant_id)
    request.session['active_restaurant_id'] = restaurant_id
    return redirect('web:admin_dashboard')


@org_required
def org_exit_restaurant(request):
    request.session.pop('active_restaurant_id', None)
    return redirect('web:org_dashboard')


# ── User management (per restaurant) ─────────────────────────────────────────

@org_required
def org_users(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    profiles = (StaffProfile.objects
                .filter(restaurant=restaurant)
                .select_related('user')
                .order_by('user__username'))
    return render(request, 'org/users.html', {
        'restaurant': restaurant,
        'profiles': profiles,
    })


@org_required
def org_user_save(request, restaurant_id, profile_id=None):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    profile = get_object_or_404(StaffProfile, id=profile_id, restaurant=restaurant) if profile_id else None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'admin').strip()

        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'org/user_form.html', {'profile': profile, 'restaurant': restaurant})

        if profile:
            user = profile.user
            if user.username != username and User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" is already taken.')
                return render(request, 'org/user_form.html', {'profile': profile, 'restaurant': restaurant})
            user.username = username
            user.email = email
            if password:
                user.set_password(password)
            user.save()
            profile.role = role
            profile.save()
            messages.success(request, f'User "{username}" updated.')
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" is already taken.')
                return render(request, 'org/user_form.html', {'profile': profile, 'restaurant': restaurant})
            if not password:
                messages.error(request, 'Password is required when creating a new user.')
                return render(request, 'org/user_form.html', {'profile': profile, 'restaurant': restaurant})
            user = User.objects.create_user(username=username, email=email, password=password, is_staff=True)
            StaffProfile.objects.create(user=user, restaurant=restaurant, role=role)
            messages.success(request, f'User "{username}" created.')

        return redirect('web:org_users', restaurant_id=restaurant_id)

    return render(request, 'org/user_form.html', {'profile': profile, 'restaurant': restaurant})


@org_required
@require_POST
def org_user_delete(request, restaurant_id, profile_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    profile = get_object_or_404(StaffProfile, id=profile_id, restaurant=restaurant)
    username = profile.user.username
    profile.user.delete()
    messages.success(request, f'User "{username}" deleted.')
    return redirect('web:org_users', restaurant_id=restaurant_id)
