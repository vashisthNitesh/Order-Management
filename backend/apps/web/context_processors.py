from django.urls import reverse


def admin_nav(request):
    if not request.path.startswith('/manage/'):
        return {}
    try:
        nav_items = [
            (reverse('web:admin_dashboard'),  '📊', 'Dashboard'),
            (reverse('web:admin_orders'),     '🧾', 'Orders'),
            (reverse('web:admin_tables'),     '🪑', 'Tables'),
            (reverse('web:admin_menu'),       '🍽️',  'Menu Items'),
            (reverse('web:admin_categories'), '📂', 'Categories'),
            (reverse('web:admin_offers'),     '🏷️',  'Offers'),
            (reverse('web:admin_staff'),      '👥', 'Staff'),
            (reverse('web:admin_logs'),       '📋', 'Logs'),
        ]
    except Exception:
        nav_items = []
    return {'nav_items': nav_items}
