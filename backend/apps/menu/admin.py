from django.contrib import admin
from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'sort_order', 'is_active', 'item_count']
    list_filter = ['restaurant', 'is_active']
    search_fields = ['name']
    ordering = ['sort_order', 'name']

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'food_type', 'is_popular', 'is_special', 'is_available']
    list_filter = ['category__restaurant', 'food_type', 'is_popular', 'is_special', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available', 'is_popular', 'is_special']
