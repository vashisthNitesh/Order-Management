from django.db import models
from django.contrib.auth.models import User
from apps.restaurants.models import Restaurant


class StaffProfile(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    WAITER = 'waiter'
    KITCHEN = 'kitchen'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (WAITER, 'Waiter'),
        (KITCHEN, 'Kitchen Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=WAITER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='staff/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"
