"""
Common constants used across the application
"""

# User roles
USER_ROLES = [
    ("admin", "Administrator"),
    ("manager", "Manager"),
    ("client", "Client"),
    ("guard", "Guard"),
    ("supervisor", "Supervisor"),
]

# Permission types
RESOURCE_TYPES = [
    ("property", "Property"),
    ("shift", "Shift"),
    ("expense", "Expense"),
    ("guard", "Guard"),
    ("client", "Client"),
]

ACTION_TYPES = [
    ("create", "Create"),
    ("read", "Read"),
    ("update", "Update"),
    ("delete", "Delete"),
    ("approve", "Approve"),
    ("assign", "Assign"),
]

ACCESS_TYPES = [
    ("owner", "Owner"),
    ("assigned_guard", "Assigned Guard"),
    ("supervisor", "Supervisor"),
    ("viewer", "Viewer"),
]

# Status choices
STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]

# Common validation messages
VALIDATION_MESSAGES = {
    "required": "This field is required.",
    "invalid_choice": "Invalid choice.",
    "positive_number": "This field must be a positive number.",
    "min_length": "This field must be at least {min_length} characters long.",
    "max_length": "This field cannot be more than {max_length} characters long.",
    "unique": "This field must be unique.",
    "invalid_email": "Enter a valid email address.",
    "passwords_dont_match": "Passwords do not match.",
}

# API response messages
API_MESSAGES = {
    "success": "Operation completed successfully.",
    "created": "Resource created successfully.",
    "updated": "Resource updated successfully.",
    "deleted": "Resource deleted successfully.",
    "not_found": "Resource not found.",
    "permission_denied": "You do not have permission to perform this action.",
    "invalid_credentials": "Invalid credentials provided.",
    "validation_error": "Validation error occurred.",
    "server_error": "Internal server error occurred.",
}

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File upload limits
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
    "text/plain",
]
