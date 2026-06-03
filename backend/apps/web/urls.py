from django.urls import path
from apps.web.views import customer, staff, admin_views

app_name = 'web'

urlpatterns = [
    # ── Customer ─────────────────────────────────────────────────────────
    path('menu/<int:table_id>/', customer.menu, name='menu'),
    path('menu/<int:table_id>/items/<int:category_id>/', customer.get_category_items, name='category_items'),
    path('order/place/<int:table_id>/', customer.place_order, name='place_order'),
    path('order/success/<str:order_number>/', customer.order_success, name='order_success'),
    path('order/track/<int:order_id>/', customer.track_order, name='track_order'),

    # ── Staff ─────────────────────────────────────────────────────────────
    path('staff/login/', staff.staff_login, name='staff_login'),
    path('staff/logout/', staff.staff_logout, name='staff_logout'),
    path('staff/orders/', staff.staff_dashboard, name='staff_dashboard'),
    path('staff/kitchen/', staff.staff_kitchen, name='staff_kitchen'),
    path('staff/order/<int:order_id>/status/', staff.update_order_status, name='update_order_status'),

    # ── Admin ─────────────────────────────────────────────────────────────
    path('manage/login/', admin_views.admin_login, name='admin_login'),
    path('manage/logout/', admin_views.admin_logout, name='admin_logout'),
    path('manage/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Tables
    path('manage/tables/', admin_views.admin_tables, name='admin_tables'),
    path('manage/tables/add/', admin_views.admin_table_save, name='admin_table_add'),
    path('manage/tables/<int:table_id>/edit/', admin_views.admin_table_save, name='admin_table_edit'),
    path('manage/tables/<int:table_id>/delete/', admin_views.admin_table_delete, name='admin_table_delete'),
    path('manage/tables/<int:table_id>/qr/', admin_views.admin_table_qr, name='admin_table_qr'),

    # Menu
    path('manage/menu/', admin_views.admin_menu, name='admin_menu'),
    path('manage/menu/add/', admin_views.admin_menu_save, name='admin_menu_add'),
    path('manage/menu/<int:item_id>/edit/', admin_views.admin_menu_save, name='admin_menu_edit'),
    path('manage/menu/<int:item_id>/delete/', admin_views.admin_menu_delete, name='admin_menu_delete'),

    # Categories
    path('manage/categories/', admin_views.admin_categories, name='admin_categories'),
    path('manage/categories/add/', admin_views.admin_category_save, name='admin_category_add'),
    path('manage/categories/<int:cat_id>/edit/', admin_views.admin_category_save, name='admin_category_edit'),
    path('manage/categories/<int:cat_id>/delete/', admin_views.admin_category_delete, name='admin_category_delete'),

    # Offers
    path('manage/offers/', admin_views.admin_offers, name='admin_offers'),
    path('manage/offers/add/', admin_views.admin_offer_save, name='admin_offer_add'),
    path('manage/offers/<int:offer_id>/edit/', admin_views.admin_offer_save, name='admin_offer_edit'),
    path('manage/offers/<int:offer_id>/delete/', admin_views.admin_offer_delete, name='admin_offer_delete'),

    # Staff management
    path('manage/staff/', admin_views.admin_staff, name='admin_staff'),
    path('manage/staff/add/', admin_views.admin_staff_save, name='admin_staff_add'),
    path('manage/staff/<int:staff_id>/edit/', admin_views.admin_staff_save, name='admin_staff_edit'),
    path('manage/staff/<int:staff_id>/delete/', admin_views.admin_staff_delete, name='admin_staff_delete'),
]
