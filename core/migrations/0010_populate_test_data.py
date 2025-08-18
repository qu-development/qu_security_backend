# Generated manually on 2025-08-18

import random
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import migrations
from django.utils import timezone

# Try to import Faker, fallback to manual generation if not available
try:
    from faker import Faker
    fake = Faker('en_US')  # English locale for coherent data
    Faker.seed(12345)  # For reproducible data
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False


def generate_unique_username(existing_usernames, prefix="", suffix=""):
    """Generate a unique username using Faker or fallback"""
    if HAS_FAKER:
        base = fake.user_name()
        if prefix:
            base = f"{prefix}.{base}"
        if suffix:
            base = f"{base}.{suffix}"
    else:
        base = f"user{random.randint(1000, 9999)}"
        if prefix:
            base = f"{prefix}.{base}"
        if suffix:
            base = f"{base}.{suffix}"

    username = base
    counter = 1
    while username in existing_usernames:
        username = f"{base}{counter}"
        counter += 1
    existing_usernames.add(username)
    return username


def generate_unique_email(existing_emails, domain="securitycorp.com"):
    """Generate a unique email using Faker or fallback"""
    if HAS_FAKER:
        base = fake.email().split('@')[0]
    else:
        base = f"user{random.randint(1000, 9999)}"

    email = f"{base}@{domain}"
    counter = 1
    while email in existing_emails:
        email = f"{base}{counter}@{domain}"
        counter += 1
    existing_emails.add(email)
    return email


def get_realistic_name():
    """Get realistic first and last name"""
    if HAS_FAKER:
        return fake.first_name(), fake.last_name()
    else:
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Maria", "James", "Jennifer"]
        last_names = ["Smith", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas"]
        return random.choice(first_names), random.choice(last_names)


def get_realistic_address():
    """Get realistic address"""
    if HAS_FAKER:
        return fake.street_address(), fake.city(), fake.state(), fake.zipcode()
    else:
        street_names = ["Main St", "Oak Ave", "Pine St", "Elm St", "Cedar Ave"]
        cities = ["Springfield", "Franklin", "Greenville", "Bristol", "Clinton"]
        states = ["CA", "TX", "FL", "NY", "IL"]
        return (
            f"{random.randint(100, 9999)} {random.choice(street_names)}",
            random.choice(cities),
            random.choice(states),
            f"{random.randint(10000, 99999)}"
        )


def get_phone_number():
    """Get realistic phone number that fits in 20 characters"""
    if HAS_FAKER:
        # Generate a simpler phone format that won't exceed 20 chars
        return f"+1{random.randint(200, 999)}{random.randint(1000000, 9999999)}"
    else:
        return f"+1{random.randint(2000000000, 9999999999)}"


def get_company_name():
    """Get realistic company name"""
    if HAS_FAKER:
        return fake.company()
    else:
        prefixes = ["Secure", "Elite", "Premium", "Pro", "Guardian", "Shield", "Fortress"]
        suffixes = ["Security", "Protection", "Services", "Corp", "Solutions", "Systems"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"


def create_test_data(apps, schema_editor):
    """Create test data: 300 clients, 120 guards, and 2000 properties"""

    # Import the current models directly instead of using historical models
    # This is safe for data migrations that don't depend on schema changes
    from django.contrib.auth.models import User
    from core.models import Client, Guard, Property
    from permissions.models import UserRole
    from django.db import transaction

    # Keep track of existing usernames and emails to avoid duplicates
    existing_usernames = set(User.objects.values_list('username', flat=True))
    existing_emails = set(User.objects.values_list('email', flat=True))

    with transaction.atomic():
        print("Starting test data generation...")

        # 1. Create 300 Clients
        print("Creating 300 clients...")
        clients = []

    for i in range(300):
        first_name, last_name = get_realistic_name()

        # Generate coherent business-oriented usernames and emails
        username = generate_unique_username(existing_usernames,
                                          prefix=first_name.lower(),
                                          suffix=last_name.lower())
        email = generate_unique_email(existing_emails, domain="businesscorp.com")

        # Create User for Client
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password='testpass123'
        )

        # Create Client with realistic financial data
        balance = Decimal(f"{random.randint(5000, 50000)}.{random.randint(0, 99):02d}")

        client = Client.objects.create(
            user=user,
            phone=get_phone_number(),
            balance=balance
        )
        clients.append(client)

        # Create UserRole for client
        UserRole.objects.create(
            user=user,
            role='client',
            is_active=random.choice([True, True, True, False])  # 75% active
        )

    print(f"Created {len(clients)} clients")

    # 2. Create 120 Guards
    print("Creating 120 guards...")
    guards = []

    for i in range(120):
        first_name, last_name = get_realistic_name()

        # Generate guard-specific usernames and emails
        username = generate_unique_username(existing_usernames,
                                          prefix=first_name.lower(),
                                          suffix=f"{last_name.lower()}.guard")
        email = generate_unique_email(existing_emails, domain="securityguards.com")

        # Create User for Guard
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password='guardpass123'
        )

        # Generate realistic guard data
        street, city, state, zipcode = get_realistic_address()
        full_address = f"{street}, {city}, {state} {zipcode}"

        # Generate realistic birth date (guards should be 21-65 years old)
        current_year = timezone.now().year
        birth_year = random.randint(current_year - 65, current_year - 21)
        birth_date = timezone.now().date().replace(
            year=birth_year,
            month=random.randint(1, 12),
            day=random.randint(1, 28)
        )

        # Generate realistic SSN format
        ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

        guard = Guard.objects.create(
            user=user,
            phone=get_phone_number(),
            ssn=ssn,
            address=full_address[:200],  # Ensure it fits in field limit
            birth_date=birth_date
        )
        guards.append(guard)

        # Create UserRole for guard
        UserRole.objects.create(
            user=user,
            role='guard',
            is_active=random.choice([True, True, True, False])  # 75% active
        )

    print(f"Created {len(guards)} guards")

    # 3. Create 2000 Properties
    print("Creating 2000 properties...")

    # Property types with realistic distributions
    property_types = [
        ('office', 0.4),      # 40% office buildings
        ('retail', 0.3),      # 30% retail stores
        ('warehouse', 0.15),  # 15% warehouses
        ('residential', 0.1), # 10% residential complexes
        ('industrial', 0.05)  # 5% industrial facilities
    ]

    properties = []
    for i in range(2000):
        # Assign property to a random client
        owner = random.choice(clients)

        # Choose property type based on realistic distribution
        rand = random.random()
        cumulative = 0
        property_type = 'office'  # default
        for ptype, prob in property_types:
            cumulative += prob
            if rand <= cumulative:
                property_type = ptype
                break

        # Generate realistic property details
        if HAS_FAKER:
            street, city, state, zipcode = get_realistic_address()

            # Generate property names based on type
            if property_type == 'office':
                name = f"{fake.company()} Office Building"
            elif property_type == 'retail':
                name = f"{city} Shopping Center"
            elif property_type == 'warehouse':
                name = f"{city} Distribution Center"
            elif property_type == 'residential':
                name = f"{fake.street_name()} Apartments"
            else:  # industrial
                name = f"{city} Industrial Complex"
        else:
            # Fallback for when Faker is not available
            cities = ["Springfield", "Franklin", "Greenville", "Bristol", "Clinton"]
            city = random.choice(cities)
            street = f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine St'])}"
            state = random.choice(["CA", "TX", "FL", "NY", "IL"])
            zipcode = f"{random.randint(10000, 99999)}"
            name = f"{city} Business Center #{i+1}"

        full_address = f"{street}, {city}, {state} {zipcode}"

        # Generate realistic pricing based on property type
        if property_type == 'office':
            base_rate = random.randint(2000, 8000)
        elif property_type == 'retail':
            base_rate = random.randint(3000, 12000)
        elif property_type == 'warehouse':
            base_rate = random.randint(1500, 5000)
        elif property_type == 'residential':
            base_rate = random.randint(1000, 4000)
        else:  # industrial
            base_rate = random.randint(2500, 10000)

        monthly_rate = Decimal(f"{base_rate}.{random.randint(0, 99):02d}")

        # Generate realistic contract dates (within last 2 years)
        start_date = fake.date_between(start_date='-2y', end_date='today') if HAS_FAKER else timezone.now().date()

        # Generate realistic hours based on property type
        if property_type in ['office', 'retail']:
            total_hours = random.choice([8, 12])  # Business hours
        elif property_type == 'residential':
            total_hours = 24  # 24/7 security
        else:  # warehouse, industrial
            total_hours = random.choice([12, 16, 24])  # Extended or 24/7

        property_obj = Property.objects.create(
            owner=owner,
            name=name[:100],  # Ensure it fits in field limit
            alias=f"PROP{i+1:04d}" if random.choice([True, False]) else None,
            address=full_address[:200],  # Ensure it fits in field limit
            monthly_rate=monthly_rate,
            contract_start_date=start_date,
            total_hours=total_hours
        )
        properties.append(property_obj)

        print(f"Created {len(properties)} properties")
        print("Test data generation completed successfully!")


def reverse_test_data(apps, schema_editor):
    """Remove test data created by this migration"""
    from django.contrib.auth.models import User
    from core.models import Client, Guard, Property
    from permissions.models import UserRole
    from django.db import transaction

    print("Removing test data...")

    with transaction.atomic():
        # Delete test data based on email domains used
        test_domains = ['businesscorp.com', 'securityguards.com', 'securitycorp.com']

    # Find test users by email domains
    test_users = User.objects.filter(
        email__iregex=r'.*@(' + '|'.join(test_domains) + ')$'
    )

    if test_users.exists():
        print(f"Found {test_users.count()} test users to remove")

        # Delete UserRoles first (to avoid foreign key constraints)
        UserRole.objects.filter(user__in=test_users).delete()

        # Delete Properties owned by test clients
        test_clients = Client.objects.filter(user__in=test_users)
        properties_deleted = Property.objects.filter(owner__in=test_clients).delete()[0]
        print(f"Deleted {properties_deleted} test properties")

        # Delete Guards
        guards_deleted = Guard.objects.filter(user__in=test_users).delete()[0]
        print(f"Deleted {guards_deleted} test guards")

        # Delete Clients
        clients_deleted = test_clients.delete()[0]
        print(f"Deleted {clients_deleted} test clients")

        # Delete Users
        users_deleted = test_users.delete()[0]
        print(f"Deleted {users_deleted} test users")

        print("Test data removed successfully!")
    else:
        print("No test data found to remove.")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_guardpropertytariff_unique_guard_property_tariff_and_more'),
        ('permissions', '0001_initial'),  # Ensure permissions app is migrated
    ]

    operations = [
        migrations.RunPython(
            create_test_data,
            reverse_code=reverse_test_data,
            atomic=False  # Allow printing progress
        ),
    ]
