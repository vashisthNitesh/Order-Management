from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.restaurants.models import Restaurant, Table
from apps.orders.models import Order, Notification
from apps.orders.utils import send_notification

class NotificationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurant = Restaurant.objects.create(
            name="Test Bistro",
            address="123 Test St",
            phone="123456789"
        )
        self.table = Table.objects.create(
            restaurant=self.restaurant,
            table_number="T1",
            capacity=4
        )
        self.user = User.objects.create_user(
            username="staff_user",
            password="password123"
        )

    def test_order_creation_triggers_staff_notification(self):
        # 1. Clear existing notifications
        Notification.objects.all().delete()

        # 2. Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="John Doe",
            special_instructions="No onions"
        )

        # 3. Verify notification created
        notifications = Notification.objects.filter(order=order)
        self.assertEqual(notifications.count(), 1)
        
        staff_notification = notifications.first()
        self.assertEqual(staff_notification.recipient_type, Notification.STAFF)
        self.assertEqual(staff_notification.title, "New Order Placed")
        self.assertIn("Order #", staff_notification.message)

    def test_order_status_change_triggers_customer_notification(self):
        # 1. Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="John Doe"
        )
        
        # Clear creation notifications
        Notification.objects.all().delete()

        # 2. Update status
        order.status = Order.PREPARING
        order.save(update_fields=['status'])

        # 3. Verify status update notification created for customer
        notifications = Notification.objects.filter(order=order)
        self.assertEqual(notifications.count(), 1)
        
        cust_notification = notifications.first()
        self.assertEqual(cust_notification.recipient_type, Notification.CUSTOMER)
        self.assertEqual(cust_notification.title, "Order Status Updated")
        self.assertIn("PREPARING", cust_notification.message)

    def test_notification_poll_view(self):
        # 1. Create order and status update
        order = Order.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="John Doe"
        )
        
        # 2. Poll notifications for staff
        response = self.client.get(f'/api/orders/notifications/poll/?restaurant_id={self.restaurant.id}&last_seen_id=0')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('notifications', data)
        self.assertGreater(len(data['notifications']), 0)
        
        # Verify the notification payload fields
        notification_payload = data['notifications'][0]
        self.assertEqual(notification_payload['recipient_type'], 'staff')
        self.assertEqual(notification_payload['title'], 'New Order Placed')

    def test_customer_order_edit_updates_items_and_notifies_staff(self):
        from apps.menu.models import Category, MenuItem
        from apps.orders.models import OrderItem, OrderLog
        
        # 1. Create a category and menu items
        category = Category.objects.create(restaurant=self.restaurant, name="Main Course")
        item1 = MenuItem.objects.create(category=category, name="Burger", price=100.00, is_available=True)
        item2 = MenuItem.objects.create(category=category, name="Pizza", price=200.00, is_available=True)
        
        # 2. Place an order via API
        payload = {
            'items': [{'menu_item_id': item1.id, 'quantity': 2}],
            'customer_name': 'Test Cust',
            'special_instructions': 'No ketchup'
        }
        import json
        response = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data['success'])
        order_id = res_data['order_id']
        
        # Verify initial order values
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.total_amount, 200.00)
        self.assertEqual(order.items.count(), 1)
        
        # 3. Edit order (session must contain order ID to allow edit)
        session = self.client.session
        session['customer_orders'] = [order_id]
        session.save()
        
        update_payload = {
            'active_order_id': order_id,
            'items': [
                {'menu_item_id': item1.id, 'quantity': 1},
                {'menu_item_id': item2.id, 'quantity': 1}
            ],
            'customer_name': 'Test Cust Updated',
            'special_instructions': 'Add mayo'
        }
        
        # Clear notifications
        Notification.objects.all().delete()
        
        response = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(update_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data_update = response.json()
        self.assertTrue(res_data_update['success'])
        
        # 4. Assert order items are updated and total recalculated
        order.refresh_from_db()
        self.assertEqual(order.total_amount, 300.00)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.customer_name, 'Test Cust Updated')
        self.assertEqual(order.special_instructions, 'Add mayo')
        
        # 5. Assert OrderLog created
        logs = OrderLog.objects.filter(order=order, action='edited')
        self.assertEqual(logs.count(), 1)
        self.assertIn("Burger", logs.first().details)
        self.assertIn("Pizza", logs.first().details)
        
        # 6. Assert Notification sent to staff
        notifications = Notification.objects.filter(order=order, recipient_type=Notification.STAFF)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().title, "Order Updated by Customer")
