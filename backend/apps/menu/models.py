from django.db import models
from apps.restaurants.models import Restaurant


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        is_new_image = False
        if self.image:
            from django.core.files.uploadedfile import UploadedFile
            try:
                if isinstance(self.image.file, UploadedFile):
                    is_new_image = True
            except Exception:
                pass
            
            if not is_new_image:
                if self.pk:
                    try:
                        old_obj = Category.objects.get(pk=self.pk)
                        if old_obj.image != self.image:
                            is_new_image = True
                    except Category.DoesNotExist:
                        is_new_image = True
                else:
                    is_new_image = True

        if is_new_image:
            from apps.menu.utils import process_image
            processed = process_image(self.image)
            if processed:
                self.image = processed

        super().save(*args, **kwargs)



class MenuItem(models.Model):
    VEG = 'veg'
    NON_VEG = 'non_veg'
    VEGAN = 'vegan'
    FOOD_TYPE_CHOICES = [
        (VEG, 'Vegetarian'),
        (NON_VEG, 'Non-Vegetarian'),
        (VEGAN, 'Vegan'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES, default=VEG)
    is_popular = models.BooleanField(default=False)
    is_special = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(default=15, help_text='Minutes')
    calories = models.IntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} - {self.category.name}"

    def save(self, *args, **kwargs):
        is_new_image = False
        if self.image:
            from django.core.files.uploadedfile import UploadedFile
            try:
                if isinstance(self.image.file, UploadedFile):
                    is_new_image = True
            except Exception:
                pass
            
            if not is_new_image:
                if self.pk:
                    try:
                        old_obj = MenuItem.objects.get(pk=self.pk)
                        if old_obj.image != self.image:
                            is_new_image = True
                    except MenuItem.DoesNotExist:
                        is_new_image = True
                else:
                    is_new_image = True

        if is_new_image:
            from apps.menu.utils import process_image
            processed = process_image(self.image)
            if processed:
                self.image = processed

        super().save(*args, **kwargs)

