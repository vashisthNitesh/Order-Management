import uuid
from django.db import models
from apps.restaurants.models import Restaurant, Table
from apps.menu.models import MenuItem


def generate_order_number():
    return str(uuid.uuid4()).replace('-', '').upper()[:8]


class Order(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PREPARING = 'preparing'
    READY = 'ready'
    SERVED = 'served'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (PREPARING, 'Preparing'),
        (READY, 'Ready'),
        (SERVED, 'Served'),
        (CANCELLED, 'Cancelled'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='paid_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - Table {self.table.table_number if self.table else 'N/A'}"

    @property
    def is_editable(self):
        return not self.is_paid

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Order.objects.get(pk=self.pk).status
            except Order.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Trigger notification safely without blocking the transaction
        try:
            from apps.orders.utils import notify_order_change
            notify_order_change(self, is_new, old_status)
        except Exception:
            pass


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name if self.menu_item else 'Deleted Item'}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class OrderLog(models.Model):
    ACTION_CHOICES = [
        ('created',        'Order Created'),
        ('item_added',     'Item Added'),
        ('item_removed',   'Item Removed'),
        ('qty_changed',    'Quantity Changed'),
        ('status_changed', 'Status Changed'),
        ('paid',           'Marked as Paid'),
        ('note_updated',   'Note Updated'),
    ]
    ACTOR_CHOICES = [
        ('staff',    'Staff'),
        ('customer', 'Customer'),
        ('system',   'System'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor_type = models.CharField(max_length=10, choices=ACTOR_CHOICES, default='system')
    actor_name = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} — {self.order.order_number}"


class Notification(models.Model):
    STAFF = 'staff'
    CUSTOMER = 'customer'
    RECIPIENT_CHOICES = [
        (STAFF, 'Staff'),
        (CUSTOMER, 'Customer'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='notifications')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES, default=STAFF)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient_type}"
