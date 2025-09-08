"""
Async task functions for S3 file operations in the QU Security backend.

These functions can be called synchronously (when USE_ASYNC_TASKS=False)
or asynchronously via SQS (when USE_ASYNC_TASKS=True).

Focus: S3 file operations for guard reports only.
"""

import logging
from typing import Any

from django.conf import settings
from django.utils import timezone

from .decorators import async_task
from .services.sqs_client import sqs_client

logger = logging.getLogger(__name__)


@async_task("process_guard_report")
def process_guard_report(report_id: int) -> dict[str, Any] | None:
    """
    Process a guard report asynchronously - S3 file operations only.

    This ensures the file is properly stored in S3 and creates a backup
    reference for the guard report.

    Args:
        report_id: ID of the GuardReport to process

    Returns:
        Processing result or None if async
    """
    try:
        from mobile.models import GuardReport

        report = GuardReport.objects.get(id=report_id)
        logger.info(
            f"Processing guard report {report_id} from {report.guard} - S3 operations only"
        )

        results = []

        # Process uploaded file if exists - S3 operations only
        if report.file:
            file_result = process_guard_report_file_s3(report)
            results.append(file_result)

        logger.info(f"Guard report {report_id} S3 processing completed")
        return {"status": "success", "report_id": report_id, "results": results}

    except Exception as e:
        logger.error(f"Failed to process guard report {report_id}: {e}")
        raise


@async_task("process_guard_report_file_s3")
def process_guard_report_file_s3(report) -> dict[str, Any]:
    """
    Process the file attached to a guard report - S3 operations only.

    This function ensures the file is properly stored in S3 and validates
    the file storage without any image processing or email notifications.

    Args:
        report: GuardReport instance

    Returns:
        S3 file processing result
    """
    try:
        if not report.file:
            return {"status": "skipped", "reason": "no_file"}

        file_path = report.file.url if hasattr(report.file, "url") else str(report.file)
        file_name = report.file.name
        file_size = report.file.size if hasattr(report.file, "size") else 0

        logger.info(
            f"Processing S3 file for report {report.id}: {file_name} ({file_size} bytes)"
        )

        # Validate S3 file storage
        s3_validation = validate_s3_file_storage(report.file)

        return {
            "status": "success",
            "report_id": report.id,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "s3_validation": s3_validation,
            "processed_at": timezone.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to process guard report file S3 operations: {e}")
        raise


def validate_s3_file_storage(file_field) -> dict[str, Any]:
    """
    Validate that a file is properly stored in S3.

    Args:
        file_field: Django FileField instance

    Returns:
        Validation result dictionary
    """
    try:
        import boto3
        from botocore.exceptions import ClientError

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
        logger.error(f"S3 validation error: {e}")
        return {"valid": False, "reason": "validation_error", "error": str(e)}


# Convenience functions for S3 file operations


def process_guard_report_file_async(report_id: int) -> dict[str, Any] | None:
    """Process a guard report file asynchronously via SQS - S3 operations only."""
    return sqs_client.send_task(
        task_name="process_guard_report_file_s3", payload={"report_id": report_id}
    )


def validate_guard_report_s3_storage(report_id: int) -> dict[str, Any] | None:
    """Validate guard report S3 storage asynchronously via SQS."""
    return sqs_client.send_task(
        task_name="validate_s3_storage", payload={"report_id": report_id}
    )
