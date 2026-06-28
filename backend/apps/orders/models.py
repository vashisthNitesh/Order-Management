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
        (PENDING, 'Received'),
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

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    def calculate_total(self):
        from decimal import Decimal
        subtotal = sum(item.subtotal for item in self.items.all())
        
        # Clear system-generated charges to recalculate clean state
        self.charges.filter(is_manual=False).delete()
        
        total_charges = 0
        active_charges = ChargeMaster.objects.filter(
            restaurant=self.restaurant,
            is_active=True
        ).order_by('sequence', 'name')
        
        for charge_config in active_charges:
            if charge_config.charge_type == ChargeMaster.PERCENTAGE:
                calculated_amount = Decimal(subtotal) * (Decimal(charge_config.amount) / Decimal('100.00'))
            else:
                calculated_amount = Decimal(charge_config.amount)
            
            calculated_amount = round(calculated_amount, 2)
            
            OrderCharge.objects.create(
                order=self,
                charge_master=charge_config,
                name=charge_config.name,
                charge_type=charge_config.charge_type,
                amount=charge_config.amount,
                calculated_amount=calculated_amount,
                sequence=charge_config.sequence,
                is_manual=False
            )
            total_charges += calculated_amount

        # Recompute and sum any manually added charges
        for manual_charge in self.charges.filter(is_manual=True):
            if manual_charge.charge_type == ChargeMaster.PERCENTAGE:
                manual_charge.calculated_amount = Decimal(subtotal) * (Decimal(manual_charge.amount) / Decimal('100.00'))
            else:
                manual_charge.calculated_amount = Decimal(manual_charge.amount)
            
            manual_charge.calculated_amount = round(manual_charge.calculated_amount, 2)
            manual_charge.save(update_fields=['calculated_amount'])
            total_charges += manual_charge.calculated_amount
            
        self.total_amount = round(Decimal(subtotal) + Decimal(total_charges), 2)
        self.save(update_fields=['total_amount'])
        return self.total_amount

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


class ChargeMaster(models.Model):
    PERCENTAGE = 'percentage'
    FIXED = 'fixed'
    
    TYPE_CHOICES = [
        (PERCENTAGE, 'Percentage'),
        (FIXED, 'Fixed Amount'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='charges_config')
    name = models.CharField(max_length=100)
    charge_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=PERCENTAGE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sequence = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence', 'name']

    def __str__(self):
        type_str = '%' if self.charge_type == self.PERCENTAGE else 'Flat'
        return f"{self.name} ({self.amount}{type_str}) - {self.restaurant.name}"


class OrderCharge(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='charges')
    charge_master = models.ForeignKey(ChargeMaster, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    charge_type = models.CharField(max_length=20, choices=ChargeMaster.TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sequence = models.IntegerField(default=0)
    is_manual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence', 'name']

    def __str__(self):
        return f"{self.name} on Order #{self.order.order_number}: {self.calculated_amount}"


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
