from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='paid_orders',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name='OrderLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('created', 'Order Created'),
                        ('item_added', 'Item Added'),
                        ('item_removed', 'Item Removed'),
                        ('qty_changed', 'Quantity Changed'),
                        ('status_changed', 'Status Changed'),
                        ('paid', 'Marked as Paid'),
                        ('note_updated', 'Note Updated'),
                    ],
                    max_length=20,
                )),
                ('actor_type', models.CharField(
                    choices=[('staff', 'Staff'), ('customer', 'Customer'), ('system', 'System')],
                    default='system', max_length=10,
                )),
                ('actor_name', models.CharField(blank=True, max_length=100)),
                ('details', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs', to='orders.order',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
