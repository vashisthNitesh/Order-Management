from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, ChargeMaster, OrderCharge


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price', 'subtotal']

    def subtotal(self, obj):
        return obj.subtotal


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'changed_by', 'created_at']


class OrderChargeInline(admin.TabularInline):
    model = OrderCharge
    extra = 1
    fields = ['name', 'charge_type', 'amount', 'calculated_amount', 'sequence', 'is_manual']
    readonly_fields = ['calculated_amount']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'restaurant', 'table', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'restaurant', 'created_at']
    search_fields = ['order_number', 'customer_name']
    readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderChargeInline, OrderStatusHistoryInline]

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        form.instance.calculate_total()


@admin.register(ChargeMaster)
class ChargeMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'charge_type', 'amount', 'sequence', 'is_active']
    list_filter = ['is_active', 'charge_type', 'restaurant']
    search_fields = ['name']
    ordering = ['restaurant', 'sequence', 'name']


@admin.register(OrderCharge)
class OrderChargeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'charge_type', 'amount', 'calculated_amount', 'sequence']
    list_filter = ['charge_type', 'created_at']
    search_fields = ['name', 'order__order_number']
    readonly_fields = ['order', 'charge_master', 'name', 'charge_type', 'amount', 'calculated_amount', 'sequence', 'created_at']
