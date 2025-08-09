from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Guard, Client, Property, Shift, Expense
from decimal import Decimal
from datetime import datetime, timedelta
import pytz


class Command(BaseCommand):
    help = 'Create sample data for testing the API endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('🗑️  Cleaning existing test data...')
            # Delete in reverse order of dependencies
            Expense.objects.filter(property__owner__user__username__startswith='test_').delete()
            Shift.objects.filter(guard__user__username__startswith='test_').delete()
            Property.objects.filter(owner__user__username__startswith='test_').delete()
            Guard.objects.filter(user__username__startswith='test_').delete()
            Client.objects.filter(user__username__startswith='test_').delete()
            User.objects.filter(username__startswith='test_').delete()
            self.stdout.write(self.style.SUCCESS('✅ Test data cleaned'))

        self.stdout.write('📊 Creating sample data...')

        # Create test users
        guard_user = User.objects.create_user(
            username='test_guard',
            email='guard@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )

        client_user = User.objects.create_user(
            username='test_client',
            email='client@example.com',
            first_name='Jane',
            last_name='Smith',
            password='testpass123'
        )

        admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='admin123'
        )

        # Create Guard
        guard = Guard.objects.create(
            user=guard_user,
            phone='+1-555-0101'
        )

        # Create Client
        client = Client.objects.create(
            user=client_user,
            phone='+1-555-0102',
            balance=Decimal('1000.00')
        )

        # Create Properties
        property1 = Property.objects.create(
            owner=client,
            address='123 Main Street, Downtown, City',
            total_hours=40
        )

        property2 = Property.objects.create(
            owner=client,
            address='456 Oak Avenue, Uptown, City',
            total_hours=60
        )

        # Create Shifts
        tz = pytz.UTC
        base_date = datetime.now(tz) - timedelta(days=7)

        shift1 = Shift.objects.create(
            guard=guard,
            property=property1,
            start_time=base_date,
            end_time=base_date + timedelta(hours=8),
            hours_worked=8
        )

        shift2 = Shift.objects.create(
            guard=guard,
            property=property2,
            start_time=base_date + timedelta(days=1),
            end_time=base_date + timedelta(days=1, hours=12),
            hours_worked=12
        )

        # Create Expenses
        expense1 = Expense.objects.create(
            property=property1,
            description='Security equipment maintenance',
            amount=Decimal('150.00')
        )

        expense2 = Expense.objects.create(
            property=property1,
            description='Emergency repair costs',
            amount=Decimal('75.50')
        )

        expense3 = Expense.objects.create(
            property=property2,
            description='Monthly security system subscription',
            amount=Decimal('99.99')
        )

        self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully!'))
        self.stdout.write('')
        self.stdout.write('📋 Created:')
        self.stdout.write(f'   👥 Users: 3 (guard, client, admin)')
        self.stdout.write(f'   🛡️  Guards: 1')
        self.stdout.write(f'   👤 Clients: 1')
        self.stdout.write(f'   🏢 Properties: 2')
        self.stdout.write(f'   ⏰ Shifts: 2')
        self.stdout.write(f'   💰 Expenses: 3')
        self.stdout.write('')
        self.stdout.write('🔑 Test Credentials:')
        self.stdout.write(f'   Guard: test_guard / testpass123')
        self.stdout.write(f'   Client: test_client / testpass123')
        self.stdout.write(f'   Admin: test_admin / admin123')
        self.stdout.write('')
        self.stdout.write('🌐 Test your API at: http://127.0.0.1:8000/swagger/')
