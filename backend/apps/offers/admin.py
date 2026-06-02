from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'restaurant', 'discount_display', 'start_date', 'end_date', 'is_active', 'usage_count']
    list_filter = ['restaurant', 'discount_type', 'is_active']
    search_fields = ['title', 'promo_code']
    filter_horizontal = ['applicable_items', 'applicable_categories']
