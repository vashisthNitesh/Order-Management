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
    # FSSAI standard: square border + filled circle inside
    cfg = {
        'veg':     {'stroke': '#15803d', 'fill': '#15803d', 'bg': '#f0fdf4'},  # green
        'non_veg': {'stroke': '#991b1b', 'fill': '#991b1b', 'bg': '#fff1f2'},  # dark red/maroon
        'egg':     {'stroke': '#b45309', 'fill': '#b45309', 'bg': '#fffbeb'},  # amber
        'vegan':   {'stroke': '#065f46', 'fill': '#065f46', 'bg': '#ecfdf5'},  # deep green
    }.get(food_type, {'stroke': '#64748b', 'fill': '#64748b', 'bg': '#f8fafc'})
    return mark_safe(
        f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;display:inline-block;vertical-align:middle">'
        f'<rect x="1" y="1" width="14" height="14" rx="2.5" fill="{cfg["bg"]}" '
        f'stroke="{cfg["stroke"]}" stroke-width="1.5"/>'
        f'<circle cx="8" cy="8" r="4" fill="{cfg["fill"]}"/>'
        f'</svg>'
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
        'pending': 'Order Received',
        'confirmed': 'Confirmed',
        'preparing': 'Preparing',
        'ready': 'Ready',
        'served': 'Served',
        'cancelled': 'Cancelled',
    }
    cls = classes.get(status, 'bg-slate-50 text-slate-600 border-slate-200/60')
    label = labels.get(status, status.title())
    return mark_safe(
        f'<span class="text-xs font-medium px-2.5 py-0.5 rounded-full border {cls}">{label}</span>'
    )


@register.filter
def get_dict_item(dictionary, key):
    if not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0)

