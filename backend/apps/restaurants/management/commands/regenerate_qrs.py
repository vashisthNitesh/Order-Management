from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Regenerate QR codes for all tables and upload them to the active storage backend'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', type=str, help='The base URL (e.g. https://my-app.onrender.com)', default='')

    def handle(self, *args, **options):
        from apps.restaurants.models import Table
        
        base_url = options['base_url']
        if not base_url:
            # Try to get from environment or fallback
            base_url = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('ALLOWED_HOSTS', '').split(',')[0]
            if not base_url or base_url == '*' or base_url == 'localhost' or base_url == '127.0.0.1':
                base_url = 'http://localhost:8000'
            elif not base_url.startswith('http'):
                base_url = f'https://{base_url}'
        
        self.stdout.write(f'Regenerating QR codes using base URL: {base_url} ...')
        
        tables = Table.objects.all()
        count = 0
        for table in tables:
            self.stdout.write(f'Regenerating QR for Table {table.table_number}...')
            table.generate_qr_code(base_url)
            table.save(update_fields=['qr_code'])
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully regenerated {count} QR code(s).'))
