from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def inr(value):
    try:
        num = float(value)
        if num == int(num):
            return f"₹{int(num):,}"
        return f"₹{num:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def food_dot(food_type):
    colors = {'veg': '#16a34a', 'non_veg': '#dc2626', 'vegan': '#059669'}
    borders = {'veg': '#16a34a', 'non_veg': '#dc2626', 'vegan': '#059669'}
    color = colors.get(food_type, '#6b7280')
    border = borders.get(food_type, '#6b7280')
    return mark_safe(
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:16px;height:16px;border:1.5px solid {border};border-radius:2px;">'
        f'<span style="width:8px;height:8px;background:{color};border-radius:50%;'
        f'display:inline-block;"></span></span>'
    )


@register.filter
def status_badge(status):
    classes = {
        'pending':   'bg-amber-50 text-amber-700 border-amber-200/60',
        'confirmed': 'bg-blue-50 text-blue-700 border-blue-200/60',
        'preparing': 'bg-orange-50 text-orange-700 border-orange-200/60',
        'ready':     'bg-emerald-50 text-emerald-700 border-emerald-200/60',
        'served':    'bg-slate-50 text-slate-600 border-slate-200/60',
        'cancelled': 'bg-rose-50 text-rose-700 border-rose-200/60',
    }
    labels = {
        'pending': 'Pending',
        'confirmed': 'Confirmed',
        'preparing': 'Preparing',
        'ready': 'Ready',
        'served': 'Served',
        'cancelled': 'Cancelled',
    }
    cls = classes.get(status, 'bg-slate-50 text-slate-600 border-slate-200/60')
    label = labels.get(status, status.title())
    return mark_safe(
        f'<span class="text-xs font-semibold px-2.5 py-1 rounded-full border {cls}">{label}</span>'
    )


@register.filter
def get_dict_item(dictionary, key):
    if not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0)

