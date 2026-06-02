from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'restaurant', 'role', 'phone', 'is_active']
    list_filter = ['restaurant', 'role', 'is_active']
    search_fields = ['user__username', 'user__email', 'user__first_name']
