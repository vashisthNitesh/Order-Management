import sys
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import InMemoryUploadedFile


CATEGORY_IMAGES = {
    'Starters':     'https://images.unsplash.com/photo-1541014741259-de529411b96a?w=800&q=80&fm=jpg&auto=format',
    'Soups':        'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=800&q=80&fm=jpg&auto=format',
    'Main Course':  'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80&fm=jpg&auto=format',
    'Pasta & Pizza':'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&fm=jpg&auto=format',
    'Burgers':      'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80&fm=jpg&auto=format',
    'Desserts':     'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=800&q=80&fm=jpg&auto=format',
    'Beverages':    'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=800&q=80&fm=jpg&auto=format',
}

ITEM_IMAGES = {
    'Bruschetta':           'https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?w=800&q=80&fm=jpg&auto=format',
    'Chicken Wings':        'https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=800&q=80&fm=jpg&auto=format',
    'Calamari':             'https://images.unsplash.com/photo-1619740455993-9d622d09d0a7?w=800&q=80&fm=jpg&auto=format',
    'Garlic Bread':         'https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?w=800&q=80&fm=jpg&auto=format',
    'Tomato Basil Soup':    'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=800&q=80&fm=jpg&auto=format',
    'French Onion Soup':    'https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=800&q=80&fm=jpg&auto=format',
    'Chicken Noodle Soup':  'https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=800&q=80&fm=jpg&auto=format',
    'Grilled Salmon':       'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=800&q=80&fm=jpg&auto=format',
    'Beef Tenderloin':      'https://images.unsplash.com/photo-1544025162-d76538b2a1c1?w=800&q=80&fm=jpg&auto=format',
    'Mushroom Risotto':     'https://images.unsplash.com/photo-1476718406336-bb5a9690ee2a?w=800&q=80&fm=jpg&auto=format',
    'Chicken Marsala':      'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=800&q=80&fm=jpg&auto=format',
    'Margherita Pizza':     'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=800&q=80&fm=jpg&auto=format',
    'Carbonara':            'https://images.unsplash.com/photo-1612874742237-6526221588e3?w=800&q=80&fm=jpg&auto=format',
    'Penne Arrabbiata':     'https://images.unsplash.com/photo-1555949258-eb67b1ef0ceb?w=800&q=80&fm=jpg&auto=format',
    'Classic Cheeseburger': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80&fm=jpg&auto=format',
    'Veggie Burger':        'https://images.unsplash.com/photo-1550547660-d9450f859349?w=800&q=80&fm=jpg&auto=format',
    'BBQ Bacon Burger':     'https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=800&q=80&fm=jpg&auto=format',
    'Tiramisu':             'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=800&q=80&fm=jpg&auto=format',
    'Chocolate Lava Cake':  'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=800&q=80&fm=jpg&auto=format',
    'Cheesecake':           'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&fm=jpg&auto=format',
    'Fresh Lemonade':       'https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=800&q=80&fm=jpg&auto=format',
    'Iced Coffee':          'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=800&q=80&fm=jpg&auto=format',
    'Mango Lassi':          'https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=800&q=80&fm=jpg&auto=format',
}


class Command(BaseCommand):
    help = 'Download food images from Unsplash and assign to categories and menu items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing images',
        )

    def handle(self, *args, **options):
        import requests
        from apps.menu.models import Category, MenuItem
        from apps.restaurants.models import Restaurant

        overwrite = options['overwrite']

        restaurant = Restaurant.objects.filter(name='The Grand Bistro').first()
        if not restaurant:
            self.stdout.write(self.style.ERROR('Restaurant "The Grand Bistro" not found. Run seed_data first.'))
            return

        def fetch_and_assign(instance, url, slug, field_name='image'):
            field = getattr(instance, field_name)
            if field and not overwrite:
                self.stdout.write(f'  SKIP  {slug} (already has image)')
                return False
            try:
                self.stdout.write(f'  GET   {slug} ...', ending='')
                self.stdout.flush()
                resp = requests.get(
                    url, timeout=30, allow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; food-image-bot/1.0)'}
                )
                if resp.status_code != 200:
                    self.stdout.write(self.style.WARNING(f' HTTP {resp.status_code}'))
                    return False

                content = resp.content
                if len(content) < 1000:
                    self.stdout.write(self.style.WARNING(' response too small, skipping'))
                    return False

                buf = BytesIO(content)
                uploaded = InMemoryUploadedFile(
                    buf, 'image', f'{slug}.jpg', 'image/jpeg', sys.getsizeof(buf), None
                )
                setattr(instance, field_name, uploaded)
                instance.save()
                self.stdout.write(self.style.SUCCESS(f' OK ({len(content) // 1024}KB → WebP)'))
                return True
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f' ERROR: {exc}'))
                return False

        self.stdout.write('\n--- Category images ---')
        ok = skip = fail = 0
        for name, url in CATEGORY_IMAGES.items():
            cat = Category.objects.filter(restaurant=restaurant, name=name).first()
            if not cat:
                self.stdout.write(self.style.WARNING(f'  NOT FOUND  {name}'))
                continue
            slug = name.lower().replace(' & ', '_').replace(' ', '_')
            result = fetch_and_assign(cat, url, f'cat_{slug}')
            if result is True:
                ok += 1
            elif result is False and cat.image and not overwrite:
                skip += 1
            else:
                fail += 1

        self.stdout.write(f'\n  Categories: {ok} uploaded, {skip} skipped, {fail} failed')

        self.stdout.write('\n--- Menu item images ---')
        ok = skip = fail = 0
        for name, url in ITEM_IMAGES.items():
            item = MenuItem.objects.filter(category__restaurant=restaurant, name=name).first()
            if not item:
                self.stdout.write(self.style.WARNING(f'  NOT FOUND  {name}'))
                continue
            slug = name.lower().replace(' ', '_')
            result = fetch_and_assign(item, url, f'item_{slug}')
            if result is True:
                ok += 1
            elif result is False and item.image and not overwrite:
                skip += 1
            else:
                fail += 1

        self.stdout.write(f'\n  Menu items: {ok} uploaded, {skip} skipped, {fail} failed')
        self.stdout.write(self.style.SUCCESS('\nDone!'))
