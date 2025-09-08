"""
Task handler functions for S3 file operations only.

Simplified handlers focused on S3 file storage validation and operations
for guard reports. No email or image processing functionality.
"""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def handle_guard_report_processing(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Handle guard report S3 file processing tasks only.

    Args:
        payload: Guard report processing data

    Returns:
        Result dictionary with S3 processing status
    """
    try:
        report_id = payload["report_id"]

        logger.info(f"Processing guard report S3 operations: {report_id}")

        # Import here to avoid circular imports
        from mobile.models import GuardReport

        report = GuardReport.objects.get(id=report_id)

        # Validate S3 file storage if file exists
        if report.file:
            s3_validation = validate_s3_file_storage_lambda(report.file)
            logger.info(f"S3 validation for report {report_id}: {s3_validation}")

            return {
                "status": "success",
                "report_id": report_id,
                "file_name": report.file.name,
                "s3_validation": s3_validation,
            }
        else:
            return {"status": "skipped", "report_id": report_id, "reason": "no_file"}

    except Exception as e:
        logger.error(f"Failed to process guard report S3 operations: {e}")
        raise


def validate_s3_file_storage_lambda(file_field) -> dict[str, Any]:
    """
    Validate that a file is properly stored in S3 (Lambda version).

    Args:
        file_field: Django FileField instance

    Returns:
        Validation result dictionary
    """
    try:
        if not file_field:
            return {"valid": False, "reason": "no_file"}

        # Extract S3 key from file path
        file_name = file_field.name

        # Initialize S3 client
        s3_client = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME)
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        # Check if file exists in S3
        try:
            s3_key = f"{settings.AWS_MEDIA_LOCATION}/{file_name}"
            response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)

            return {
                "valid": True,
                "bucket": bucket_name,
                "s3_key": s3_key,
                "size": response.get("ContentLength", 0),
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType"),
                "validated_at": timezone.now().isoformat(),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return {
                    "valid": False,
                    "reason": "file_not_found_in_s3",
                    "error": str(e),
                }
            else:
                return {"valid": False, "reason": "s3_error", "error": str(e)}

    except Exception as e:
        logger.error(f"S3 validation error in Lambda: {e}")
        return {"valid": False, "reason": "validation_error", "error": str(e)}
