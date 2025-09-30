import os
import re
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify

from core.models import Guard


class GuardImportService:
    """Optimized service for importing guards from Excel files in AWS Lambda"""

    # Expected column names in Excel
    EXPECTED_COLUMNS = {
        "name": "NOMBRE Y APELLIDOS",
        "income": "INGRESOS",
        "address": "Address",
        "ssn": "Social Security",
        "observations": "Observaciones",
    }

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.created_guards = []
        self.skipped_rows = []
        # Pre-fetch existing data to reduce database queries
        self.existing_usernames = set()
        self.existing_users = {}
        self.existing_guards = set()

        # Dynamic batch size based on environment
        self.BATCH_SIZE = self._get_optimal_batch_size()

    def _get_optimal_batch_size(self) -> int:
        """Get optimal batch size based on environment"""
        # AWS Lambda environment
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            memory_mb = int(os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", 512))
            if memory_mb >= 1024:
                return 500  # Large memory, much bigger batches for performance
            elif memory_mb >= 512:
                return 200  # Medium memory, bigger batches
            else:
                return 100  # Small memory, still decent batches

        # Local development - use very large batches
        return 1000  # Process all at once if possible

    def process_excel_file(
        self,
        file_path: str,
        create_users: bool = True,
        default_password: str = None,
    ) -> dict:
        """
        Optimized process Excel file and create Guard records for AWS Lambda

        Args:
            file_path: Path to Excel file
            create_users: Whether to create User accounts
            default_password: Default password for created users

        Returns:
            Dict with results summary
        """
        try:
            # Use settings password if none provided
            if default_password is None:
                default_password = settings.GUARD_DEFAULT_PASSWORD

            # Read Excel file with optimized settings
            df = pd.read_excel(
                file_path,
                engine="openpyxl",
                dtype=str,  # Read all as strings to avoid type conversion overhead
                na_filter=False,  # Don't convert empty cells to NaN
            )

            # Validate columns
            self._validate_columns(df)

            # Pre-fetch existing data to minimize database queries
            self._prefetch_existing_data()

            # Process in batches to control memory usage
            total_rows = len(df)
            processed_rows = 0

            # For small files, process all at once for maximum performance
            if total_rows <= 500:
                self._process_all_at_once(df, create_users, default_password)
            else:
                # For large files, use batch processing

                for batch_start in range(0, total_rows, self.BATCH_SIZE):
                    batch_end = min(batch_start + self.BATCH_SIZE, total_rows)
                    batch_df = df.iloc[batch_start:batch_end]

                    # Process batch without atomic transaction for better performance
                    batch_users = []
                    batch_guards = []

                    for index, row in batch_df.iterrows():
                        try:
                            user, guard_data = self._prepare_row_data(
                                row, index + 2, create_users, default_password, set()
                            )
                            if user and guard_data:
                                batch_users.append(user)
                                batch_guards.append(guard_data)
                        except Exception as e:
                            self.errors.append(f"Row {index + 2}: {str(e)}")
                            continue

                    # Bulk create users and guards efficiently
                    if batch_users and create_users:
                        self._bulk_create_users(batch_users)

                    if batch_guards:
                        self._bulk_create_guards(batch_guards, create_users)

                    processed_rows += len(batch_df)

                    # Clean up batch data to free memory
                    del batch_df, batch_users, batch_guards

            # Clean up DataFrame to free memory
            del df

            return self._get_results_summary()

        except Exception as e:
            self.errors.append(f"File processing error: {str(e)}")
            return self._get_results_summary()

    def _process_all_at_once(
        self, df: pd.DataFrame, create_users: bool, default_password: str
    ) -> None:
        """Process entire file at once for maximum performance with small files"""
        all_users = []
        all_guards = []
        temp_usernames = set()  # Track usernames in this batch to avoid duplicates

        # Process all rows at once
        for index, row in df.iterrows():
            try:
                user, guard_data = self._prepare_row_data(
                    row, index + 2, create_users, default_password, temp_usernames
                )
                if user and guard_data:
                    all_users.append(user)
                    all_guards.append(guard_data)
                    temp_usernames.add(user["username"])  # Track for uniqueness
                elif guard_data:  # Always add guard_data even if no user_data
                    all_guards.append(guard_data)
            except Exception as e:
                self.errors.append(f"Row {index + 2}: {str(e)}")
                continue

        # Create all users at once
        if all_users and create_users:
            self._bulk_create_users(all_users)

        # Create all guards at once
        if all_guards:
            self._bulk_create_guards(all_guards, create_users)

    def _prefetch_existing_data(self) -> None:
        """Pre-fetch existing data to minimize database queries - OPTIMIZED"""

        # Efficient single query for usernames
        self.existing_usernames = set(User.objects.values_list("username", flat=True))

        # Efficient single query for users - only load what we need
        users_data = User.objects.values("id", "username", "first_name", "last_name")
        self.existing_users = {}
        user_id_to_username = {}

        for user_data in users_data:
            # Create minimal User objects to avoid full object loading
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
            self.existing_users[user_data["username"]] = user
            user_id_to_username[user_data["id"]] = user_data["username"]

        # Efficient single query for existing guards
        self.existing_guards = set(Guard.objects.values_list("user_id", flat=True))

    def _prepare_row_data(
        self,
        row: pd.Series,
        row_number: int,
        create_users: bool,
        default_password: str,
        temp_usernames: set = None,
    ) -> tuple[dict | None, dict | None]:
        """Prepare data for a single row without database operations"""
        # Extract data
        full_name = self._clean_string(row.get(self.EXPECTED_COLUMNS["name"], ""))
        if not full_name:
            self.skipped_rows.append(f"Row {row_number}: Empty name")
            return None, None

        income_str = str(row.get(self.EXPECTED_COLUMNS["income"], "0"))
        address = self._clean_string(row.get(self.EXPECTED_COLUMNS["address"], ""))
        ssn = self._clean_string(row.get(self.EXPECTED_COLUMNS["ssn"], ""))
        observations = self._clean_string(
            row.get(self.EXPECTED_COLUMNS["observations"], "")
        )

        # Parse income
        income = self._parse_income(income_str)

        # Generate username from name
        username = self._generate_username(full_name, temp_usernames or set())

        # Split name into first and last name
        first_name, last_name = self._split_name(full_name)

        # Prepare user data
        user_data = None
        if create_users and username not in self.existing_usernames:
            user_data = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": default_password,
                "is_active": True,
            }
            # DON'T add to existing_usernames here! Only after actual creation

        # Prepare guard data
        guard_data = {
            "username": username,
            "address": address,
            "ssn": ssn,
            "income": income,
            "observations": observations,
            "row_number": row_number,
        }

        return user_data, guard_data

    def _bulk_create_users(self, batch_users: list[dict]) -> None:
        """Bulk create users efficiently with minimal queries"""
        try:
            users_to_create = []
            usernames_to_create = set()

            # Pre-hash the password ONCE instead of 121 times
            from django.contrib.auth.hashers import make_password

            default_password = (
                batch_users[0]["password"]
                if batch_users
                else settings.GUARD_DEFAULT_PASSWORD
            )
            hashed_password = make_password(default_password)

            for user_data in batch_users:
                username = user_data["username"]
                # Skip if already exists or already processed in this batch
                if (
                    username not in self.existing_usernames
                    and username not in usernames_to_create
                ):
                    user = User(
                        username=username,
                        first_name=user_data["first_name"],
                        last_name=user_data["last_name"],
                        is_active=user_data["is_active"],
                        password=hashed_password,  # Use pre-hashed password - MUCH faster!
                    )
                    # DON'T call user.set_password() - it's too slow (46+ seconds)!
                    users_to_create.append(user)
                    usernames_to_create.add(username)

            # Bulk create with ignore_conflicts for safety
            if users_to_create:
                # Use a transaction to ensure consistency
                with transaction.atomic():
                    User.objects.bulk_create(
                        users_to_create,
                        ignore_conflicts=True,
                        batch_size=500,  # Larger batch for better performance
                    )

                    # CRITICAL: Refresh cache with all newly created users
                    # Get all users that were just created
                    new_users = User.objects.filter(username__in=usernames_to_create)

                    for user in new_users:
                        self.existing_users[user.username] = user
                        self.existing_usernames.add(user.username)

        except Exception as e:
            self.errors.append(f"Bulk user creation error: {str(e)}")

    def _bulk_create_guards(self, batch_guards: list[dict], create_users: bool) -> None:
        """Bulk create guards efficiently"""
        try:
            guards_to_create = []
            usernames_processed = set()

            for guard_data in batch_guards:
                username = guard_data["username"]

                # Skip duplicates within the batch
                if username in usernames_processed:
                    continue
                usernames_processed.add(username)

                user = None
                # Always try to find the user, regardless of create_users flag
                user = self.existing_users.get(username)
                if not user:
                    # Try to get from database if not in cache (user might have been just created)
                    try:
                        user = User.objects.get(username=username)
                        self.existing_users[username] = user  # Update cache
                    except User.DoesNotExist:
                        self.errors.append(
                            f"Row {guard_data['row_number']}: User {username} not found"
                        )
                        continue

                # Check if guard already exists for this user
                if user and user.id in self.existing_guards:
                    self.warnings.append(
                        f"Row {guard_data['row_number']}: Guard for user {username} already exists"
                    )
                    continue

                # Only create if user exists and guard doesn't exist
                if user:
                    guard = Guard(
                        user=user,
                        address=guard_data["address"],
                        ssn=guard_data["ssn"],
                        phone="",  # Default empty phone
                        is_armed=False,  # Default not armed
                    )
                    guards_to_create.append(guard)
                    self.existing_guards.add(user.id)  # Mark as processed

            # Bulk create guards efficiently
            if guards_to_create:
                try:
                    # Use bulk_create for much better performance
                    created_guards = Guard.objects.bulk_create(
                        guards_to_create,
                        ignore_conflicts=True,
                        batch_size=500,  # Larger batch for better performance
                    )
                    created_count = len(created_guards)
                    self.created_guards.extend(created_guards)

                except Exception:
                    # Fallback to individual creation only if bulk fails

                    created_count = 0
                    for guard in guards_to_create:
                        try:
                            if not Guard.objects.filter(user=guard.user).exists():
                                guard.save()
                                self.created_guards.append(guard)
                                created_count += 1
                        except Exception as individual_error:
                            self.errors.append(
                                f"Error creating guard for {guard.user.username}: {str(individual_error)}"
                            )

            else:
                created_count = 0

        except Exception as e:
            self.errors.append(f"Bulk guard creation error: {str(e)}")

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist"""
        required_cols = [self.EXPECTED_COLUMNS["name"]]  # Only name is truly required
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    def _clean_string(self, value) -> str:
        """Clean and normalize string values"""
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _parse_income(self, income_str: str) -> Decimal:
        """Parse income string to Decimal (handle European format)"""
        if not income_str or pd.isna(income_str):
            return Decimal("0")

        # Remove any currency symbols and spaces
        income_str = str(income_str).strip()

        # Handle European format (dots as thousands separator, comma as decimal)
        # Examples: "4.840,00" -> "4840.00", "49.257,32" -> "49257.32"
        if "," in income_str and "." in income_str:
            # Both comma and dot present - European format
            income_str = income_str.replace(".", "").replace(",", ".")
        elif "," in income_str and "." not in income_str:
            # Only comma - treat as decimal separator
            income_str = income_str.replace(",", ".")

        # Remove any non-numeric characters except dots
        income_str = re.sub(r"[^0-9.]", "", income_str)

        try:
            return Decimal(income_str)
        except (ValueError, TypeError):
            return Decimal("0")

    def _generate_username(self, full_name: str, temp_usernames: set = None) -> str:
        """Generate unique username from full name - OPTIMIZED"""
        # Basic cleanup and slug generation
        base_username = slugify(full_name).replace("-", "_")[:30]

        # Ensure uniqueness using CACHE instead of database queries
        username = base_username
        counter = 1
        temp_usernames = temp_usernames or set()
        # Use existing cache AND temp batch usernames instead of hitting database
        while username in self.existing_usernames or username in temp_usernames:
            username = f"{base_username}_{counter}"
            counter += 1

        return username

    def _split_name(self, full_name: str) -> tuple[str, str]:
        """Split full name into first and last name"""
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            # More than 2 parts - first word is first name, rest is last name
            return parts[0], " ".join(parts[1:])

    def _get_results_summary(self) -> dict:
        """Get summary of import results"""
        return {
            "total_processed": len(self.created_guards) + len(self.skipped_rows),
            "guards_created": len(self.created_guards),
            "rows_skipped": len(self.skipped_rows),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "created_guards": self.created_guards,
            "errors": self.errors,
            "warnings": self.warnings,
            "skipped_rows": self.skipped_rows,
        }
