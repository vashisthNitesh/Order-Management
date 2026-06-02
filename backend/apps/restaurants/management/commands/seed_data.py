from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Import models here to avoid circular imports
        from apps.restaurants.models import Restaurant, Table
        from apps.menu.models import Category, MenuItem
        from apps.staff.models import StaffProfile
        from apps.offers.models import Offer

        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@restaurant.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin123'))

        # Create restaurant
        restaurant, _ = Restaurant.objects.get_or_create(
            name='The Grand Bistro',
            defaults={
                'address': '123 Main Street, New York, NY 10001',
                'phone': '+1 (555) 123-4567',
                'email': 'info@grandbistro.com',
                'description': 'A premium dining experience with a blend of continental and local flavors.',
                'is_active': True,
            }
        )
        self.stdout.write(f'Restaurant: {restaurant.name}')

        # Create tables
        for i in range(1, 11):
            Table.objects.get_or_create(
                restaurant=restaurant,
                table_number=str(i),
                defaults={'capacity': 4 if i <= 7 else 6}
            )
        self.stdout.write('Created 10 tables')

        # Create staff users
        staff_data = [
            {'username': 'manager1', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@bistro.com', 'role': 'manager'},
            {'username': 'waiter1', 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah@bistro.com', 'role': 'waiter'},
            {'username': 'kitchen1', 'first_name': 'Mike', 'last_name': 'Chen', 'email': 'mike@bistro.com', 'role': 'kitchen'},
        ]
        for sd in staff_data:
            if not User.objects.filter(username=sd['username']).exists():
                user = User.objects.create_user(
                    username=sd['username'],
                    email=sd['email'],
                    first_name=sd['first_name'],
                    last_name=sd['last_name'],
                    password='staff123'
                )
                StaffProfile.objects.create(user=user, restaurant=restaurant, role=sd['role'])
                self.stdout.write(f'Created staff: {sd["username"]} / staff123')

        # Create categories
        categories_data = [
            {'name': 'Starters', 'icon': '🥗', 'sort_order': 1},
            {'name': 'Soups', 'icon': '🍲', 'sort_order': 2},
            {'name': 'Main Course', 'icon': '🍽️', 'sort_order': 3},
            {'name': 'Pasta & Pizza', 'icon': '🍕', 'sort_order': 4},
            {'name': 'Burgers', 'icon': '🍔', 'sort_order': 5},
            {'name': 'Desserts', 'icon': '🍰', 'sort_order': 6},
            {'name': 'Beverages', 'icon': '🥤', 'sort_order': 7},
        ]
        categories = {}
        for cd in categories_data:
            cat, _ = Category.objects.get_or_create(
                restaurant=restaurant, name=cd['name'],
                defaults={'icon': cd['icon'], 'sort_order': cd['sort_order']}
            )
            categories[cd['name']] = cat
        self.stdout.write('Created categories')

        # Create menu items (prices in INR)
        menu_items = [
            # Starters
            {'cat': 'Starters', 'name': 'Bruschetta', 'desc': 'Toasted bread with tomatoes, garlic, and fresh basil', 'price': '199', 'food_type': 'veg', 'is_popular': True},
            {'cat': 'Starters', 'name': 'Chicken Wings', 'desc': 'Crispy wings with choice of sauce', 'price': '349', 'food_type': 'non_veg', 'is_popular': True},
            {'cat': 'Starters', 'name': 'Calamari', 'desc': 'Lightly breaded fried squid with marinara sauce', 'price': '299', 'food_type': 'non_veg'},
            {'cat': 'Starters', 'name': 'Garlic Bread', 'desc': 'Freshly baked bread with garlic butter', 'price': '149', 'food_type': 'veg'},
            # Soups
            {'cat': 'Soups', 'name': 'Tomato Basil Soup', 'desc': 'Creamy tomato soup with fresh basil', 'price': '199', 'food_type': 'veg', 'is_popular': True},
            {'cat': 'Soups', 'name': 'French Onion Soup', 'desc': 'Classic onion soup with gruyere crouton', 'price': '249', 'food_type': 'veg'},
            {'cat': 'Soups', 'name': 'Chicken Noodle Soup', 'desc': 'Hearty soup with vegetables and noodles', 'price': '229', 'food_type': 'non_veg'},
            # Main Course
            {'cat': 'Main Course', 'name': 'Grilled Salmon', 'desc': 'Atlantic salmon with lemon butter sauce and seasonal vegetables', 'price': '699', 'food_type': 'non_veg', 'is_popular': True, 'is_special': True},
            {'cat': 'Main Course', 'name': 'Beef Tenderloin', 'desc': '250g premium beef with mushroom sauce', 'price': '899', 'food_type': 'non_veg', 'is_special': True},
            {'cat': 'Main Course', 'name': 'Mushroom Risotto', 'desc': 'Creamy arborio rice with wild mushrooms and parmesan', 'price': '449', 'food_type': 'veg', 'is_popular': True},
            {'cat': 'Main Course', 'name': 'Chicken Marsala', 'desc': 'Pan-seared chicken in Marsala wine sauce', 'price': '549', 'food_type': 'non_veg'},
            # Pasta & Pizza
            {'cat': 'Pasta & Pizza', 'name': 'Margherita Pizza', 'desc': 'Classic pizza with tomato sauce, mozzarella, and basil', 'price': '349', 'food_type': 'veg', 'is_popular': True},
            {'cat': 'Pasta & Pizza', 'name': 'Carbonara', 'desc': 'Spaghetti with pancetta, eggs, pecorino, and black pepper', 'price': '399', 'food_type': 'non_veg'},
            {'cat': 'Pasta & Pizza', 'name': 'Penne Arrabbiata', 'desc': 'Spicy tomato sauce with garlic and red chili', 'price': '299', 'food_type': 'vegan'},
            # Burgers
            {'cat': 'Burgers', 'name': 'Classic Cheeseburger', 'desc': 'Beef patty with cheddar, lettuce, tomato, onion', 'price': '329', 'food_type': 'non_veg', 'is_popular': True},
            {'cat': 'Burgers', 'name': 'Veggie Burger', 'desc': 'Plant-based patty with all the fixings', 'price': '279', 'food_type': 'veg'},
            {'cat': 'Burgers', 'name': 'BBQ Bacon Burger', 'desc': 'Double patty with bacon, BBQ sauce, and caramelized onions', 'price': '449', 'food_type': 'non_veg', 'is_special': True},
            # Desserts
            {'cat': 'Desserts', 'name': 'Tiramisu', 'desc': 'Classic Italian dessert with mascarpone and espresso', 'price': '249', 'food_type': 'veg', 'is_popular': True},
            {'cat': 'Desserts', 'name': 'Chocolate Lava Cake', 'desc': 'Warm chocolate cake with molten center and vanilla ice cream', 'price': '279', 'food_type': 'veg', 'is_special': True},
            {'cat': 'Desserts', 'name': 'Cheesecake', 'desc': 'New York style cheesecake with berry compote', 'price': '229', 'food_type': 'veg'},
            # Beverages
            {'cat': 'Beverages', 'name': 'Fresh Lemonade', 'desc': 'Freshly squeezed lemonade with mint', 'price': '129', 'food_type': 'vegan'},
            {'cat': 'Beverages', 'name': 'Iced Coffee', 'desc': 'Cold brew coffee with cream', 'price': '179', 'food_type': 'veg'},
            {'cat': 'Beverages', 'name': 'Mango Lassi', 'desc': 'Creamy yogurt-based mango drink', 'price': '149', 'food_type': 'veg', 'is_popular': True},
        ]

        for item_data in menu_items:
            cat = categories[item_data['cat']]
            MenuItem.objects.get_or_create(
                category=cat,
                name=item_data['name'],
                defaults={
                    'description': item_data['desc'],
                    'price': Decimal(item_data['price']),
                    'food_type': item_data['food_type'],
                    'is_popular': item_data.get('is_popular', False),
                    'is_special': item_data.get('is_special', False),
                    'is_available': True,
                }
            )
        self.stdout.write('Created menu items')

        # Create offers
        now = timezone.now()
        offers_data = [
            {
                'title': 'Happy Hour Special',
                'description': '20% off all beverages from 4-7 PM',
                'discount_type': 'percentage',
                'discount_value': '20',
                'start_date': now,
                'end_date': now + timedelta(days=30),
            },
            {
                'title': 'Weekend Brunch Deal',
                'description': 'Flat ₹100 off on orders above ₹499',
                'discount_type': 'fixed',
                'discount_value': '100',
                'min_order_amount': '499',
                'start_date': now,
                'end_date': now + timedelta(days=60),
            },
        ]
        for od in offers_data:
            Offer.objects.get_or_create(
                restaurant=restaurant,
                title=od['title'],
                defaults={**od, 'is_active': True}
            )
        self.stdout.write('Created offers')

        self.stdout.write(self.style.SUCCESS('\nDatabase seeded successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:   admin / admin123')
        self.stdout.write('  Manager: manager1 / staff123')
        self.stdout.write('  Waiter:  waiter1 / staff123')
        self.stdout.write('  Kitchen: kitchen1 / staff123')
