from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('web:staff_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('web:admin_login')
        is_admin = request.user.is_superuser
        if not is_admin:
            try:
                role = request.user.staff_profile.role
                is_admin = role in ('admin', 'manager')
            except Exception:
                is_admin = False
        if not is_admin:
            messages.error(request, "You don't have permission to access the admin panel.")
            return redirect('web:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper
