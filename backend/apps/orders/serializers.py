from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from apps.menu.serializers import MenuItemSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_image = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'menu_item_image', 'quantity', 'unit_price', 'subtotal', 'special_instructions']

    def get_menu_item_image(self, obj):
        request = self.context.get('request')
        if obj.menu_item and obj.menu_item.image and request:
            return request.build_absolute_uri(obj.menu_item.image.url)
        return None


class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_instructions']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'changed_by_name', 'note', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'restaurant', 'table', 'table_number', 'order_number',
            'status', 'total_amount', 'special_instructions', 'customer_name',
            'customer_phone', 'items', 'status_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['restaurant', 'table', 'special_instructions', 'customer_name', 'customer_phone', 'items']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Order must contain at least one item.")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        total = 0
        for item_data in items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']
            unit_price = menu_item.price
            subtotal = unit_price * quantity
            total += subtotal
            OrderItem.objects.create(
                order=order,
                unit_price=unit_price,
                **item_data
            )

        order.total_amount = total
        order.save(update_fields=['total_amount'])

        OrderStatusHistory.objects.create(order=order, status=Order.PENDING)
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status', 'special_instructions']

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        if new_status != instance.status:
            OrderStatusHistory.objects.create(
                order=instance,
                status=new_status,
                changed_by=self.context['request'].user if self.context.get('request') else None
            )
        return super().update(instance, validated_data)
