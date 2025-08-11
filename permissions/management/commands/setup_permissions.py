"""
Django management command to setup initial permissions and groups
"""

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Client, Guard
from permissions.models import ResourcePermission, UserRole
from permissions.utils import PermissionManager


class Command(BaseCommand):
    help = "Setup initial permissions, groups, and roles for QU Security Backend"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset all permissions and groups before creating new ones",
        )
        parser.add_argument(
            "--create-admin",
            action="store_true",
            help="Create a default admin user",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up permissions and groups..."))

        if options["reset"]:
            self.reset_permissions()

        with transaction.atomic():
            self.create_groups()
            self.create_resource_permissions()
            self.setup_default_permissions()

            if options["create_admin"]:
                self.create_admin_user()

        self.stdout.write(
            self.style.SUCCESS("Successfully setup permissions and groups!")
        )

    def reset_permissions(self):
        """Reset all custom permissions and groups"""
        self.stdout.write("Resetting permissions and groups...")

        # Delete custom groups
        Group.objects.filter(
            name__in=["Administrators", "Managers", "Clients", "Guards"]
        ).delete()

        # Delete custom resource permissions
        ResourcePermission.objects.all().delete()

        # Delete user roles
        UserRole.objects.all().delete()

        self.stdout.write(self.style.WARNING("Reset completed."))

    def create_groups(self):
        """Create user groups with Django permissions"""
        self.stdout.write("Creating user groups...")

        # Define groups and their permissions
        group_permissions = {
            "Administrators": {
                "description": "System administrators with full access",
                "permissions": [
                    # User permissions
                    "add_user",
                    "change_user",
                    "delete_user",
                    "view_user",
                    # Guard permissions
                    "add_guard",
                    "change_guard",
                    "delete_guard",
                    "view_guard",
                    # Client permissions
                    "add_client",
                    "change_client",
                    "delete_client",
                    "view_client",
                    # Property permissions
                    "add_property",
                    "change_property",
                    "delete_property",
                    "view_property",
                    # Shift permissions
                    "add_shift",
                    "change_shift",
                    "delete_shift",
                    "view_shift",
                    # Expense permissions
                    "add_expense",
                    "change_expense",
                    "delete_expense",
                    "view_expense",
                ],
            },
            "Managers": {
                "description": "Managers with operational access",
                "permissions": [
                    "view_user",
                    "change_user",
                    "add_guard",
                    "change_guard",
                    "view_guard",
                    "add_client",
                    "change_client",
                    "view_client",
                    "add_property",
                    "change_property",
                    "view_property",
                    "add_shift",
                    "change_shift",
                    "view_shift",
                    "add_expense",
                    "change_expense",
                    "view_expense",
                ],
            },
            "Clients": {
                "description": "Property owners with limited access",
                "permissions": [
                    "view_property",
                    "change_property",
                    "view_shift",
                    "add_expense",
                    "change_expense",
                    "view_expense",
                ],
            },
            "Guards": {
                "description": "Security guards with shift access",
                "permissions": [
                    "add_shift",
                    "change_shift",
                    "view_shift",
                    "view_property",
                ],
            },
        }

        for group_name, group_data in group_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(f"Created group: {group_name}")
            else:
                self.stdout.write(f"Group already exists: {group_name}")

            # Clear existing permissions
            group.permissions.clear()

            # Add permissions to group
            for perm_codename in group_data["permissions"]:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Permission {perm_codename} not found")
                    )

    def create_resource_permissions(self):
        """Create custom resource permissions"""
        self.stdout.write("Creating resource permissions...")

        resources = ["user", "guard", "client", "property", "shift", "expense"]
        actions = ["create", "read", "update", "delete"]

        for resource in resources:
            for action in actions:
                permission, created = ResourcePermission.objects.get_or_create(
                    resource_type=resource,
                    action=action,
                    defaults={"description": f"Can {action} {resource}"},
                )

                if created:
                    self.stdout.write(f"Created permission: {action}_{resource}")

    def setup_default_permissions(self):
        """Setup default permission assignments"""
        self.stdout.write("Setting up default permission assignments...")

        # Admin role permissions
        admin_permissions = [
            ("user", ["create", "read", "update", "delete"]),
            ("guard", ["create", "read", "update", "delete"]),
            ("client", ["create", "read", "update", "delete"]),
            ("property", ["create", "read", "update", "delete"]),
            ("shift", ["create", "read", "update", "delete"]),
            ("expense", ["create", "read", "update", "delete"]),
        ]

        # Manager role permissions
        manager_permissions = [
            ("user", ["read", "update"]),
            ("guard", ["create", "read", "update"]),
            ("client", ["create", "read", "update"]),
            ("property", ["create", "read", "update"]),
            ("shift", ["create", "read", "update"]),
            ("expense", ["create", "read", "update"]),
        ]

        # Client role permissions
        client_permissions = [
            ("property", ["read", "update"]),
            ("shift", ["read"]),
            ("expense", ["create", "read", "update", "delete"]),
        ]

        # Guard role permissions
        guard_permissions = [
            ("property", ["read"]),
            ("shift", ["create", "read", "update"]),
        ]

        # Store default permissions for later assignment
        self.default_permissions = {
            "admin": admin_permissions,
            "manager": manager_permissions,
            "client": client_permissions,
            "guard": guard_permissions,
        }

    def create_admin_user(self):
        """Create a default admin user"""
        self.stdout.write("Creating admin user...")

        username = "admin"
        email = "admin@qusecurity.local"
        password = "admin123"

        admin_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "first_name": "System",
                "last_name": "Administrator",
            },
        )

        if created:
            admin_user.set_password(password)
            admin_user.save()

            # Add to Administrators group
            admin_group = Group.objects.get(name="Administrators")
            admin_user.groups.add(admin_group)

            # Create UserRole
            PermissionManager.assign_role(admin_user, "admin")

            self.stdout.write(
                self.style.SUCCESS(f"Admin user created: {username} / {password}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Admin user already exists: {username}")
            )

    def create_test_users(self):
        """Create test users for each role"""
        self.stdout.write("Creating test users...")

        test_users = [
            {
                "username": "manager1",
                "email": "manager@qusecurity.local",
                "password": "manager123",
                "role": "manager",
                "group": "Managers",
                "first_name": "Test",
                "last_name": "Manager",
            },
            {
                "username": "client1",
                "email": "client@qusecurity.local",
                "password": "client123",
                "role": "client",
                "group": "Clients",
                "first_name": "Test",
                "last_name": "Client",
            },
            {
                "username": "guard1",
                "email": "guard@qusecurity.local",
                "password": "guard123",
                "role": "guard",
                "group": "Guards",
                "first_name": "Test",
                "last_name": "Guard",
            },
        ]

        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "is_active": True,
                },
            )

            if created:
                user.set_password(user_data["password"])
                user.save()

                # Add to group
                group = Group.objects.get(name=user_data["group"])
                user.groups.add(group)

                # Assign role
                PermissionManager.assign_role(user, user_data["role"])

                # Create profile based on role
                if user_data["role"] == "client":
                    Client.objects.create(
                        user=user,
                        company_name=f"{user.first_name}'s Properties",
                        contact_info=user.email,
                    )
                elif user_data["role"] == "guard":
                    Guard.objects.create(
                        user=user,
                        license_number=f"LIC{user.id:04d}",
                        phone="+1234567890",
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Test user created: {user_data["username"]} ({user_data["role"]})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Test user already exists: {user_data["username"]}'
                    )
                )
