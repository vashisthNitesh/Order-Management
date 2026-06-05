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
