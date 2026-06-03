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
        'pending':   'bg-yellow-100 text-yellow-800 border-yellow-300',
        'confirmed': 'bg-blue-100 text-blue-800 border-blue-300',
        'preparing': 'bg-orange-100 text-orange-800 border-orange-300',
        'ready':     'bg-green-100 text-green-800 border-green-300',
        'served':    'bg-gray-100 text-gray-600 border-gray-300',
        'cancelled': 'bg-red-100 text-red-700 border-red-300',
    }
    labels = {
        'pending': 'Received', 'confirmed': 'Confirmed',
        'preparing': 'Preparing', 'ready': 'Ready',
        'served': 'Served', 'cancelled': 'Cancelled',
    }
    cls = classes.get(status, 'bg-gray-100 text-gray-600')
    label = labels.get(status, status.title())
    return mark_safe(
        f'<span class="text-xs font-semibold px-2 py-0.5 rounded-full border {cls}">{label}</span>'
    )
