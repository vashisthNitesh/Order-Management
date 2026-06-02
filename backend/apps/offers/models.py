from django.db import models
from django.utils import timezone
from apps.restaurants.models import Restaurant
from apps.menu.models import MenuItem, Category


class Offer(models.Model):
    PERCENTAGE = 'percentage'
    FIXED = 'fixed'

    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, 'Percentage'),
        (FIXED, 'Fixed Amount'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='offers/', null=True, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=PERCENTAGE)
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    applicable_items = models.ManyToManyField(MenuItem, blank=True, related_name='offers')
    applicable_categories = models.ManyToManyField(Category, blank=True, related_name='offers')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    promo_code = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.discount_value}{'%' if self.discount_type == self.PERCENTAGE else ''}"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date or now > self.end_date:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True

    @property
    def discount_display(self):
        if self.discount_type == self.PERCENTAGE:
            return f"{self.discount_value}% OFF"
        return f"${self.discount_value} OFF"
