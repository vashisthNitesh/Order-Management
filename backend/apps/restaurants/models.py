import uuid
import qrcode
import io
import base64
from django.db import models
from django.core.files.base import ContentFile


class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='restaurant/', null=True, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    table_number = models.CharField(max_length=20)
    capacity = models.IntegerField(default=4)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['restaurant', 'table_number']
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number} - {self.restaurant.name}"

    def generate_qr_code(self, base_url=None):
        if not base_url:
            from django.conf import settings
            import os
            base_url = getattr(settings, 'QR_BASE_URL', None)
            if not base_url:
                base_url = os.environ.get('RENDER_EXTERNAL_URL')
            if not base_url:
                base_url = os.environ.get('SITE_URL') or os.environ.get('BACKEND_URL')
            if not base_url:
                base_url = 'http://localhost:8000'

        # Ensure scheme is prepended if not present
        if base_url and not base_url.startswith('http'):
            base_url = f"https://{base_url}"

        url = f"{base_url}/menu/{self.id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_table_{self.table_number}_{self.restaurant.id}.png'
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        return self.qr_code

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])

