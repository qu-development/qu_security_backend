import os
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify

from core.models import Client, Property


class PropertyImportService:
    """Optimized service for importing properties from Excel files"""

    # Expected column names in Excel
    EXPECTED_COLUMNS = {
        "property_name": "PROPERTY NAME",
        "alias": "SOBRE NOMBRE",
        "owner": "PROPERTY OWNER",
    }

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.created_properties = []
        self.skipped_rows = []
        # Pre-fetch existing data to reduce database queries
        self.existing_usernames = set()
        self.existing_users = {}
        self.existing_clients = {}
        self.existing_properties = set()

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
        create_clients: bool = True,
        default_password: str = None,
    ) -> dict:
        """
        Optimized process Excel file and create Property records

        Args:
            file_path: Path to Excel file
            create_clients: Whether to create Client accounts
            default_password: Default password for created client users

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

            # For small files, process all at once for maximum performance
            if total_rows <= 500:
                print(
                    f"Small file detected ({total_rows} rows), processing all at once for maximum speed..."
                )
                self._process_all_at_once(df, create_clients, default_password)
            else:
                # For large files, use batch processing
                print(
                    f"Large file detected ({total_rows} rows), using batch processing..."
                )
                self._process_in_batches(df, create_clients, default_password)

            # Clean up DataFrame to free memory
            del df

            return self._get_results_summary()

        except Exception as e:
            self.errors.append(f"File processing error: {str(e)}")
            return self._get_results_summary()

    def _process_all_at_once(
        self, df: pd.DataFrame, create_clients: bool, default_password: str
    ) -> None:
        """Process entire file at once for maximum performance with small files"""
        all_users = []
        all_clients = []
        all_properties = []
        temp_usernames = set()  # Track usernames in this batch to avoid duplicates

        # Process all rows at once
        for index, row in df.iterrows():
            try:
                user_data, client_data, property_data = self._prepare_row_data(
                    row, index + 2, create_clients, default_password, temp_usernames
                )

                if user_data:
                    all_users.append(user_data)
                    temp_usernames.add(user_data["username"])

                if client_data:
                    all_clients.append(client_data)

                if property_data:
                    all_properties.append(property_data)

            except Exception as e:
                self.errors.append(f"Row {index + 2}: {str(e)}")
                continue

        # Create all users at once
        if all_users and create_clients:
            print(f"Creating {len(all_users)} users...")
            self._bulk_create_users(all_users)

        # Create all clients at once
        if all_clients and create_clients:
            print(f"Creating {len(all_clients)} clients...")
            self._bulk_create_clients(all_clients)

        # Create all properties at once
        if all_properties:
            print(f"Creating {len(all_properties)} properties...")
            self._bulk_create_properties(all_properties)

        print(f"✅ Successfully processed {len(df)} rows")

    def _process_in_batches(
        self, df: pd.DataFrame, create_clients: bool, default_password: str
    ) -> None:
        """Process large files in batches"""
        total_rows = len(df)
        processed_rows = 0

        for batch_start in range(0, total_rows, self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, total_rows)
            batch_df = df.iloc[batch_start:batch_end]

            # Process batch
            batch_users = []
            batch_clients = []
            batch_properties = []
            temp_usernames = set()

            for index, row in batch_df.iterrows():
                try:
                    user_data, client_data, property_data = self._prepare_row_data(
                        row, index + 2, create_clients, default_password, temp_usernames
                    )

                    if user_data:
                        batch_users.append(user_data)
                        temp_usernames.add(user_data["username"])

                    if client_data:
                        batch_clients.append(client_data)

                    if property_data:
                        batch_properties.append(property_data)

                except Exception as e:
                    self.errors.append(f"Row {index + 2}: {str(e)}")
                    continue

            # Bulk create for this batch
            if batch_users and create_clients:
                self._bulk_create_users(batch_users)

            if batch_clients and create_clients:
                self._bulk_create_clients(batch_clients)

            if batch_properties:
                self._bulk_create_properties(batch_properties)

            processed_rows += len(batch_df)

            # Log progress
            if processed_rows % 500 == 0:
                print(f"Processed {processed_rows}/{total_rows} rows")

            # Clean up batch data
            del batch_df, batch_users, batch_clients, batch_properties

    def _prefetch_existing_data(self) -> None:
        """Pre-fetch existing data to minimize database queries"""
        print("Pre-loading existing data...")

        # Efficient single query for usernames
        self.existing_usernames = set(User.objects.values_list("username", flat=True))

        # Efficient single query for users
        users_data = User.objects.values("id", "username", "first_name", "last_name")
        self.existing_users = {}

        for user_data in users_data:
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
            self.existing_users[user_data["username"]] = user

        # Efficient single query for existing clients
        clients_data = Client.objects.select_related("user").values(
            "id", "user__username", "user_id"
        )
        self.existing_clients = {}
        for client_data in clients_data:
            self.existing_clients[client_data["user__username"]] = client_data["id"]

        # Efficient single query for existing properties (by address to avoid duplicates)
        self.existing_properties = set(
            Property.objects.values_list("address", flat=True)
        )

        print(
            f"Pre-loaded: {len(self.existing_usernames)} users, {len(self.existing_clients)} clients, {len(self.existing_properties)} properties"
        )

    def _prepare_row_data(
        self,
        row: pd.Series,
        row_number: int,
        create_clients: bool,
        default_password: str,
        temp_usernames: set = None,
    ) -> tuple[dict | None, dict | None, dict | None]:
        """Prepare data for a single row without database operations"""

        # Extract data
        property_name = self._clean_string(
            row.get(self.EXPECTED_COLUMNS["property_name"], "")
        )
        alias = self._clean_string(row.get(self.EXPECTED_COLUMNS["alias"], ""))
        owner_name = self._clean_string(row.get(self.EXPECTED_COLUMNS["owner"], ""))

        if not property_name:
            self.skipped_rows.append(f"Row {row_number}: Empty property name")
            return None, None, None

        if not owner_name:
            self.skipped_rows.append(f"Row {row_number}: Empty owner name")
            return None, None, None

        # Extract address from property name (everything before the last part which might be the name)
        address = property_name.strip()

        # Generate property name from address if not clear
        name_parts = address.split()
        # Use ternary operator as suggested by ruff
        name = " ".join(name_parts[:3]) if len(name_parts) > 1 else address

        # Generate username from owner name
        username = self._generate_username(owner_name, temp_usernames or set())

        # Split owner name into first and last name
        first_name, last_name = self._split_name(owner_name)

        # Prepare user data
        user_data = None
        if create_clients and username not in self.existing_usernames:
            user_data = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": default_password,
                "is_active": True,
            }

        # Prepare client data
        client_data = None
        if create_clients and username not in self.existing_clients:
            client_data = {
                "username": username,
                "phone": "",  # Default empty phone
                "balance": Decimal("0.00"),  # Default balance
            }

        # Prepare property data
        property_data = {
            "owner_username": username,
            "name": name,
            "alias": alias,
            "address": address,
            "description": "",  # Default empty description
            "row_number": row_number,
        }

        return user_data, client_data, property_data

    def _bulk_create_users(self, batch_users: list[dict]) -> None:
        """Bulk create users efficiently with minimal queries"""
        try:
            # Pre-hash the password ONCE instead of N times
            from django.contrib.auth.hashers import make_password

            default_password = (
                batch_users[0]["password"]
                if batch_users
                else settings.GUARD_DEFAULT_PASSWORD
            )
            hashed_password = make_password(default_password)

            users_to_create = []
            usernames_to_create = set()

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
                        password=hashed_password,  # Use pre-hashed password
                    )
                    users_to_create.append(user)
                    usernames_to_create.add(username)

            # Bulk create with ignore_conflicts for safety
            if users_to_create:
                with transaction.atomic():
                    User.objects.bulk_create(
                        users_to_create, ignore_conflicts=True, batch_size=500
                    )

                    # Refresh cache with newly created users
                    new_users = User.objects.filter(username__in=usernames_to_create)

                    for user in new_users:
                        self.existing_users[user.username] = user
                        self.existing_usernames.add(user.username)

        except Exception as e:
            self.errors.append(f"Bulk user creation error: {str(e)}")

    def _bulk_create_clients(self, batch_clients: list[dict]) -> None:
        """Bulk create clients efficiently"""
        try:
            clients_to_create = []
            usernames_processed = set()

            for client_data in batch_clients:
                username = client_data["username"]

                # Skip duplicates within the batch
                if username in usernames_processed:
                    continue
                usernames_processed.add(username)

                # Find the user
                user = self.existing_users.get(username)
                if not user:
                    # Try to get from database if not in cache
                    try:
                        user = User.objects.get(username=username)
                        self.existing_users[username] = user
                    except User.DoesNotExist:
                        self.errors.append(
                            f"User {username} not found for client creation"
                        )
                        continue

                # Check if client already exists
                if username in self.existing_clients:
                    continue

                # Create client
                client = Client(
                    user=user,
                    phone=client_data["phone"],
                    balance=client_data["balance"],
                )
                clients_to_create.append(client)

            # Bulk create clients
            if clients_to_create:
                created_clients = Client.objects.bulk_create(
                    clients_to_create, ignore_conflicts=True, batch_size=500
                )

                # Update cache
                for client in created_clients:
                    if hasattr(client, "user") and client.user:
                        self.existing_clients[client.user.username] = client.id

        except Exception as e:
            self.errors.append(f"Bulk client creation error: {str(e)}")

    def _bulk_create_properties(self, batch_properties: list[dict]) -> None:
        """Bulk create properties efficiently"""
        try:
            properties_to_create = []
            addresses_processed = set()

            for property_data in batch_properties:
                address = property_data["address"]
                owner_username = property_data["owner_username"]

                # Skip duplicates within the batch
                if address in addresses_processed:
                    continue
                addresses_processed.add(address)

                # Check if property already exists
                if address in self.existing_properties:
                    self.warnings.append(
                        f"Row {property_data['row_number']}: Property with address '{address}' already exists"
                    )
                    continue

                # Find the client (owner)
                client_id = self.existing_clients.get(owner_username)
                if not client_id:
                    # Try to get from database
                    try:
                        client = Client.objects.select_related("user").get(
                            user__username=owner_username
                        )
                        client_id = client.id
                        self.existing_clients[owner_username] = client_id
                    except Client.DoesNotExist:
                        self.errors.append(
                            f"Row {property_data['row_number']}: Client {owner_username} not found"
                        )
                        continue

                # Create property
                property_obj = Property(
                    owner_id=client_id,
                    name=property_data["name"],
                    alias=property_data["alias"],
                    address=address,
                    description=property_data["description"],
                )
                properties_to_create.append(property_obj)
                self.existing_properties.add(address)  # Mark as processed

            # Bulk create properties
            if properties_to_create:
                created_properties = Property.objects.bulk_create(
                    properties_to_create, ignore_conflicts=True, batch_size=500
                )
                self.created_properties.extend(created_properties)

        except Exception as e:
            self.errors.append(f"Bulk property creation error: {str(e)}")

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist"""
        required_cols = [
            self.EXPECTED_COLUMNS["property_name"],
            self.EXPECTED_COLUMNS["owner"],
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    def _clean_string(self, value) -> str:
        """Clean and normalize string values"""
        if pd.isna(value):
            return ""
        return str(value).strip()

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
            "total_processed": len(self.created_properties) + len(self.skipped_rows),
            "properties_created": len(self.created_properties),
            "rows_skipped": len(self.skipped_rows),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "created_properties": self.created_properties,
            "errors": self.errors,
            "warnings": self.warnings,
            "skipped_rows": self.skipped_rows,
        }
