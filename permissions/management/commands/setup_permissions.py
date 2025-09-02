from django.core.management.base import BaseCommand

from permissions.utils import PermissionManager


class Command(BaseCommand):
    help = "Setup default groups and permissions for the application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of groups even if they exist",
        )

    def handle(self, *args, **options):
        self.stdout.write("Setting up default groups and permissions...")

        try:
            PermissionManager.setup_default_groups()
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully created default groups and permissions"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error setting up permissions: {e}"))
            raise e
