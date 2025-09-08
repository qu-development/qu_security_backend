"""
Async task decorators for SQS-based task processing.
"""

import functools
import logging
from collections.abc import Callable

from django.conf import settings

from ..services.sqs_client import sqs_client

logger = logging.getLogger(__name__)


def async_task(
    task_name: str, delay_seconds: int = 0, message_group_id: str | None = None
):
    """
    Decorator to make a function asynchronous using SQS.

    When USE_ASYNC_TASKS is True, the function will be sent to SQS for processing
    by a Lambda function. When False, the function executes synchronously.

    Args:
        task_name: Name of the task for SQS message routing
        delay_seconds: Delay before message becomes available (0-900 seconds)
        message_group_id: Message group ID for FIFO queues

    Usage:
        @async_task('send_notification_email')
        def send_notification_email(user_id, message):
            # Function implementation
            pass

        # Call the function normally
        send_notification_email(123, "Hello World")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if settings.USE_ASYNC_TASKS:
                # Send to SQS for async processing
                payload = {
                    "function_name": func.__name__,
                    "module": func.__module__,
                    "args": args,
                    "kwargs": kwargs,
                }

                logger.info(f"Sending async task '{task_name}' to SQS")
                return sqs_client.send_task(
                    task_name=task_name,
                    payload=payload,
                    delay_seconds=delay_seconds,
                    message_group_id=message_group_id,
                )
            else:
                # Execute synchronously
                logger.debug(f"Executing task '{task_name}' synchronously")
                return func(*args, **kwargs)

        # Add metadata to the function
        wrapper._is_async_task = True  # type: ignore[attr-defined]
        wrapper._task_name = task_name  # type: ignore[attr-defined]
        wrapper._original_func = func  # type: ignore[attr-defined]

        return wrapper

    return decorator


def task(func: Callable) -> Callable:
    """
    Simple task decorator that uses the function name as the task name.

    This is a convenience decorator that automatically uses the function name
    as the SQS task name.

    Usage:
        @task
        def process_guard_report(report_id):
            # Function implementation
            pass
    """
    task_name = f"{func.__module__}.{func.__name__}"
    return async_task(task_name)(func)


class TaskRegistry:
    """
    Registry to keep track of all async tasks for Lambda function routing.
    """

    def __init__(self):
        self._tasks: dict[str, Callable] = {}

    def register(self, task_name: str, func: Callable):
        """Register a task function."""
        self._tasks[task_name] = func
        logger.debug(f"Registered task: {task_name}")

    def get_task(self, task_name: str) -> Callable | None:
        """Get a registered task function."""
        return self._tasks.get(task_name)

    def list_tasks(self) -> dict[str, Callable]:
        """List all registered tasks."""
        return self._tasks.copy()


# Global task registry
task_registry = TaskRegistry()


def register_task(task_name: str):
    """
    Decorator to register a task function in the global registry.

    This is useful for Lambda functions to discover and execute tasks.

    Usage:
        @register_task('send_email')
        def send_email_handler(payload):
            # Implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        task_registry.register(task_name, func)
        return func

    return decorator
