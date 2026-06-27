# Patch Django context copying bug in Python 3.14+
try:
    from django.template.context import BaseContext
    def safe_copy(self):
        dup = self.__class__.__new__(self.__class__)
        dup.__dict__.update(self.__dict__)
        dup.dicts = self.dicts[:]
        return dup
    BaseContext.__copy__ = safe_copy
except Exception:
    pass

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

    def test_order_detail_view_success(self):
        order = Order.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="John Doe"
        )
        response = self.client.get(f'/api/orders/{order.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], order.id)
        self.assertEqual(data['status'], 'pending')

    def test_get_category_items_success(self):
        from apps.menu.models import Category, MenuItem
        category = Category.objects.create(restaurant=self.restaurant, name="Dessert")
        item1 = MenuItem.objects.create(category=category, name="Ice Cream", price=50.00, is_available=True)
        item2 = MenuItem.objects.create(category=category, name="Cake", price=60.00, is_available=False)

        response = self.client.get(f'/menu/{self.table.id}/items/{category.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['name'], "Ice Cream")

    def test_order_append_success(self):
        from apps.menu.models import Category, MenuItem
        from apps.orders.models import OrderItem, OrderLog
        import json

        category = Category.objects.create(restaurant=self.restaurant, name="Main Course")
        item1 = MenuItem.objects.create(category=category, name="Burger", price=100.00, is_available=True)
        item2 = MenuItem.objects.create(category=category, name="Pizza", price=200.00, is_available=True)

        # 1. Place initial order
        initial_payload = {
            'items': [{'menu_item_id': item1.id, 'quantity': 1}],
            'customer_name': 'Alice',
            'special_instructions': 'Extra cheese'
        }
        res1 = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(initial_payload),
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 200)
        order_id = res1.json()['order_id']

        # Update order status to cooking/preparing in KDS
        order = Order.objects.get(id=order_id)
        order.status = Order.PREPARING
        order.save()

        # 2. Place a second order (representing Browse & Order More)
        append_payload = {
            'items': [{'menu_item_id': item2.id, 'quantity': 2}],
            'customer_name': 'Alice Updated',
            'special_instructions': 'Hurry up'
        }
        
        # Clear notifications
        Notification.objects.all().delete()

        res2 = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(append_payload),
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 200)
        res_data = res2.json()
        self.assertTrue(res_data['success'])
        self.assertEqual(res_data['order_id'], order_id) # Same order

        # 3. Assert items are appended and status is reset
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PENDING) # Reset back to pending
        self.assertEqual(order.items.count(), 2) # Both item1 and item2 exist
        self.assertEqual(order.total_amount, 500.00) # 1x100 + 2x200 = 500
        self.assertEqual(order.special_instructions, 'Extra cheese | Hurry up')
        self.assertEqual(order.customer_name, 'Alice Updated')

        # 4. Verify OrderLog action is item_added
        log = OrderLog.objects.filter(order=order, action='item_added').first()
        self.assertIsNotNone(log)
        self.assertIn("Pizza", log.details)

        # 5. Verify notification to staff is triggered
        staff_notifications = Notification.objects.filter(order=order, recipient_type=Notification.STAFF)
        self.assertEqual(staff_notifications.count(), 1)
        self.assertEqual(staff_notifications.first().title, "New Items Added to Order")

    def test_order_charges_calculation(self):
        from apps.menu.models import Category, MenuItem
        from apps.orders.models import ChargeMaster, OrderCharge
        
        # 1. Create ChargeMaster configurations for self.restaurant
        ChargeMaster.objects.create(
            restaurant=self.restaurant,
            name="GST",
            charge_type=ChargeMaster.PERCENTAGE,
            amount=5.00,
            sequence=1
        )
        ChargeMaster.objects.create(
            restaurant=self.restaurant,
            name="Service Charge",
            charge_type=ChargeMaster.PERCENTAGE,
            amount=10.00,
            sequence=2
        )
        ChargeMaster.objects.create(
            restaurant=self.restaurant,
            name="Packaging Charge",
            charge_type=ChargeMaster.FIXED,
            amount=30.00,
            sequence=3
        )
        
        # 2. Place an order
        category = Category.objects.create(restaurant=self.restaurant, name="Mains")
        item = MenuItem.objects.create(category=category, name="Pasta", price=200.00, is_available=True)
        
        import json
        payload = {
            'items': [{'menu_item_id': item.id, 'quantity': 2}], # Subtotal: 400.00
            'customer_name': 'Charlie'
        }
        response = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order_id = response.json()['order_id']
        
        order = Order.objects.get(id=order_id)
        
        # 3. Assert correct calculation of charges:
        # GST = 400 * 0.05 = 20.00
        # Service Charge = 400 * 0.10 = 40.00
        # Packaging = 30.00
        # Total = 400 + 20 + 40 + 30 = 490.00
        
        self.assertEqual(order.subtotal, 400.00)
        self.assertEqual(order.total_amount, 490.00)
        
        # Verify applied charges in OrderCharge table
        charges = list(order.charges.all().order_by('sequence'))
        self.assertEqual(len(charges), 3)
        
        self.assertEqual(charges[0].name, "GST")
        self.assertEqual(charges[0].calculated_amount, 20.00)
        
        self.assertEqual(charges[1].name, "Service Charge")
        self.assertEqual(charges[1].calculated_amount, 40.00)
        
        self.assertEqual(charges[2].name, "Packaging Charge")
        self.assertEqual(charges[2].calculated_amount, 30.00)

    def test_order_manual_charges(self):
        from apps.menu.models import Category, MenuItem
        from apps.orders.models import ChargeMaster, OrderCharge
        
        # 1. Create system ChargeMaster GST configuration
        ChargeMaster.objects.create(
            restaurant=self.restaurant,
            name="GST",
            charge_type=ChargeMaster.PERCENTAGE,
            amount=5.00,
            sequence=1
        )
        
        # 2. Place an order
        category = Category.objects.create(restaurant=self.restaurant, name="Mains")
        item = MenuItem.objects.create(category=category, name="Pasta", price=200.00, is_available=True)
        
        import json
        payload = {
            'items': [{'menu_item_id': item.id, 'quantity': 1}], # Subtotal: 200.00
            'customer_name': 'Manual Charlie'
        }
        response = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order_id = response.json()['order_id']
        
        order = Order.objects.get(id=order_id)
        # Verify subtotal: 200, GST: 10, Total: 210
        self.assertEqual(order.subtotal, 200.00)
        self.assertEqual(order.total_amount, 210.00)
        
        # 3. Create a manual discount (-50) and a manual percentage tips (10%)
        OrderCharge.objects.create(
            order=order,
            name="Admin Discount",
            charge_type=ChargeMaster.FIXED,
            amount=-50.00,
            calculated_amount=-50.00,
            sequence=5,
            is_manual=True
        )
        OrderCharge.objects.create(
            order=order,
            name="Waiter Tip",
            charge_type=ChargeMaster.PERCENTAGE,
            amount=10.00,
            calculated_amount=20.00,
            sequence=6,
            is_manual=True
        )
        
        # 4. Calculate total again to test manual charges integration
        order.calculate_total()
        
        # Grand total should be:
        # Subtotal: 200.00
        # GST (System): 10.00
        # Admin Discount (Manual): -50.00
        # Waiter Tip (Manual 10%): 20.00
        # Grand Total = 200.00 + 10.00 - 50.00 + 20.00 = 180.00
        self.assertEqual(order.total_amount, 180.00)
        
        # 5. Verify that system GST recalculates and keeps manual charges
        charges = list(order.charges.all().order_by('sequence'))
        self.assertEqual(len(charges), 3)
        self.assertEqual(charges[0].name, "GST")
        self.assertEqual(charges[1].name, "Admin Discount")
        self.assertEqual(charges[2].name, "Waiter Tip")

    def test_customer_cannot_edit_non_pending_order(self):
        from apps.menu.models import Category, MenuItem
        from apps.orders.models import OrderItem
        category = Category.objects.create(restaurant=self.restaurant, name="Mains")
        item = MenuItem.objects.create(category=category, name="Pasta", price=200.00, is_available=True)
        
        # 1. Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="Bob",
            status=Order.PENDING
        )
        OrderItem.objects.create(order=order, menu_item=item, quantity=1, unit_price=200.00)
        order.calculate_total()
        
        # Set session
        session = self.client.session
        session['customer_orders'] = [order.id]
        session.save()
        
        # Change status to CONFIRMED
        order.status = Order.CONFIRMED
        order.save()
        
        # 2. Try to edit order items via POST - should be forbidden (403 or redirect)
        import json
        payload = {
            'active_order_id': order.id,
            'items': [{'menu_item_id': item.id, 'quantity': 5}],
            'customer_name': 'Bob'
        }
        res = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403)
        
        # 3. Try to update note - should redirect back to tracking
        res2 = self.client.post(
            f'/order/edit/{order.order_number}/note/',
            data={'special_instructions': 'Hurry up'}
        )
        self.assertEqual(res2.status_code, 302)
        order.refresh_from_db()
        self.assertNotEqual(order.special_instructions, 'Hurry up')

    def test_cannot_place_order_with_unavailable_items(self):
        from apps.menu.models import Category, MenuItem
        category = Category.objects.create(restaurant=self.restaurant, name="Drinks")
        item1 = MenuItem.objects.create(category=category, name="Soda", price=50.00, is_available=True)
        item2 = MenuItem.objects.create(category=category, name="Juice", price=100.00, is_available=False) # Unavailable
        
        import json
        payload = {
            'items': [
                {'menu_item_id': item1.id, 'quantity': 1},
                {'menu_item_id': item2.id, 'quantity': 2}
            ],
            'customer_name': 'Soda Lover'
        }
        res = self.client.post(
            f'/order/place/{self.table.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        order_id = res.json()['order_id']
        order = Order.objects.get(id=order_id)
        
        # Should only have Soda, not Juice
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().menu_item, item1)
        self.assertEqual(order.subtotal, 50.00)

    def test_staff_mark_paid(self):
        from django.contrib.auth.models import User
        from apps.menu.models import Category, MenuItem
        from apps.orders.models import OrderItem
        category = Category.objects.create(restaurant=self.restaurant, name="Drinks")
        item = MenuItem.objects.create(category=category, name="Soda", price=50.00, is_available=True)
        
        order = Order.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="Bob",
            status=Order.SERVED
        )
        OrderItem.objects.create(order=order, menu_item=item, quantity=1, unit_price=50.00)
        order.calculate_total()
        
        # Login staff user
        staff_user = User.objects.create_user(username='waiter1', password='password123')
        from apps.staff.models import StaffProfile
        StaffProfile.objects.create(user=staff_user, restaurant=self.restaurant, role='waiter')
        self.client.login(username='waiter1', password='password123')
        
        # Mark paid
        res = self.client.post(f'/staff/order/{order.id}/mark-paid/')
        self.assertEqual(res.status_code, 302)
        
        order.refresh_from_db()
        self.assertTrue(order.is_paid)
        self.assertIsNotNone(order.paid_at)
        self.assertEqual(order.paid_by, staff_user)

    def test_restaurant_branding_settings(self):
        from django.contrib.auth.models import User
        # 1. Login admin user
        admin_user = User.objects.create_superuser(username='admin1', password='password123', email='admin@bistro.com')
        self.client.login(username='admin1', password='password123')
        
        # 2. Get settings page
        res = self.client.get('/manage/settings/')
        self.assertEqual(res.status_code, 200)
        
        # 3. Post branding modifications
        payload = {
            'name': 'Bistro Updated',
            'phone': '1234567890',
            'email': 'update@bistro.com',
            'address': 'New Street 1',
            'description': 'Updated description',
            'primary_color': '#ff0000',
            'accent_color': '#00ff00'
        }
        res2 = self.client.post('/manage/settings/', data=payload)
        self.assertEqual(res2.status_code, 302) # Redirects back to settings
        
        # 4. Verify DB changes
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, 'Bistro Updated')
        self.assertEqual(self.restaurant.primary_color, '#ff0000')
        self.assertEqual(self.restaurant.accent_color, '#00ff00')

    def test_admin_charges_crud(self):
        from decimal import Decimal
        from django.contrib.auth.models import User
        from apps.orders.models import ChargeMaster
        
        # 1. Login admin
        admin_user = User.objects.create_superuser(username='admin_charge_test', password='password123', email='admin@charge.com')
        self.client.login(username='admin_charge_test', password='password123')
        
        # 2. Get charges list view
        res = self.client.get('/manage/charges/')
        self.assertEqual(res.status_code, 200)
        
        # 3. Create charge via POST
        payload = {
            'name': 'GST 5%',
            'charge_type': 'percentage',
            'amount': '5.00',
            'sequence': '10',
            'is_active': 'on'
        }
        res2 = self.client.post('/manage/charges/add/', data=payload)
        self.assertEqual(res2.status_code, 302) # Redirect to admin_charges
        
        # 4. Verify charge created in DB
        charge = ChargeMaster.objects.get(name='GST 5%')
        self.assertEqual(charge.amount, Decimal('5.00'))
        self.assertEqual(charge.charge_type, 'percentage')
        self.assertEqual(charge.sequence, 10)
        self.assertTrue(charge.is_active)
        
        # 5. Edit charge
        payload_edit = {
            'name': 'GST 5% Updated',
            'charge_type': 'fixed',
            'amount': '15.00',
            'sequence': '20',
            'is_active': 'on'
        }
        res3 = self.client.post(f'/manage/charges/{charge.id}/edit/', data=payload_edit)
        self.assertEqual(res3.status_code, 302)
        
        charge.refresh_from_db()
        self.assertEqual(charge.name, 'GST 5% Updated')
        self.assertEqual(charge.amount, Decimal('15.00'))
        self.assertEqual(charge.charge_type, 'fixed')
        self.assertEqual(charge.sequence, 20)
        
        # 6. Delete charge
        res4 = self.client.post(f'/manage/charges/{charge.id}/delete/')
        self.assertEqual(res4.status_code, 302)
        self.assertFalse(ChargeMaster.objects.filter(id=charge.id).exists())
