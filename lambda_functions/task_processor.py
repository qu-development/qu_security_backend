"""
Main Lambda function for processing SQS tasks.

This function receives messages from SQS and routes them to appropriate
task handlers based on the task name.
"""

import json
import logging
import os
import sys
from typing import Any

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qu_security.settings")

import django

django.setup()

from .task_handlers import handle_guard_report_processing  # noqa: E402

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler for processing SQS messages.

    Args:
        event: Lambda event containing SQS records
        context: Lambda context object

    Returns:
        Response dictionary with processing results
    """
    logger.info(f"Processing {len(event.get('Records', []))} SQS messages")

    processed_count = 0
    failed_count = 0
    errors = []

    for record in event.get("Records", []):
        try:
            # Parse the SQS message
            message_body = json.loads(record["body"])
            task_name = message_body.get("task")
            payload = message_body.get("payload", {})
            timestamp = message_body.get("timestamp")

            logger.info(f"Processing task: {task_name} (timestamp: {timestamp})")

            # Route to appropriate task handler
            process_task(task_name, payload)

            logger.info(f"Task {task_name} completed successfully")
            processed_count += 1

        except Exception as e:
            logger.error(f"Failed to process SQS record: {e}", exc_info=True)
            failed_count += 1
            errors.append(str(e))

    # Return processing summary
    response = {
        "statusCode": 200 if failed_count == 0 else 207,  # 207 = Multi-Status
        "body": json.dumps(
            {"processed": processed_count, "failed": failed_count, "errors": errors}
        ),
    }

    logger.info(
        f"Processing complete. Success: {processed_count}, Failed: {failed_count}"
    )
    return response


def process_task(task_name: str, payload: dict[str, Any]) -> Any:
    """
    Route a task to the appropriate handler function.

    Args:
        task_name: Name of the task to process
        payload: Task payload data

    Returns:
        Task execution result

    Raises:
        ValueError: If task name is not recognized
    """
    # Task handler registry - S3 operations only
    task_handlers = {
        "process_guard_report": handle_guard_report_processing,
        "process_guard_report_file_s3": handle_guard_report_processing,
        "validate_s3_storage": handle_guard_report_processing,
    }

    # Handle dynamic task names (module.function format)
    if task_name not in task_handlers and "." in task_name:
        return handle_dynamic_task(task_name, payload)

    handler = task_handlers.get(task_name)
    if not handler:
        raise ValueError(f"Unknown task: {task_name}")

    return handler(payload)


def handle_dynamic_task(task_name: str, payload: dict[str, Any]) -> Any:
    """
    Handle dynamically named tasks (module.function format).

    This allows calling any Django function asynchronously by specifying
    the full module path and function name.

    Args:
        task_name: Full module path to the function (e.g., 'myapp.tasks.my_function')
        payload: Task payload containing function args and kwargs

    Returns:
        Function execution result
    """
    try:
        # Extract module and function name
        module_path, function_name = task_name.rsplit(".", 1)

        # Import the module
        module = __import__(module_path, fromlist=[function_name])
        func = getattr(module, function_name)

        # Extract function arguments
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})

        # Execute the function
        logger.info(f"Executing dynamic task: {task_name}")
        return func(*args, **kwargs)

    except Exception as e:
        logger.error(f"Failed to execute dynamic task {task_name}: {e}")
        raise
