"""
AWS SQS client wrapper for sending asynchronous tasks.
"""

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class SQSTaskClient:
    """
    AWS SQS client for sending asynchronous task messages.

    This client handles sending task messages to SQS queues for processing
    by Lambda functions. It provides error handling, logging, and message
    formatting.
    """

    def __init__(self):
        """Initialize the SQS client."""
        if not settings.USE_ASYNC_TASKS:
            logger.warning("Async tasks are disabled. Tasks will run synchronously.")
            return

        if not settings.AWS_SQS_QUEUE_URL:
            raise ValueError(
                "AWS_SQS_QUEUE_URL must be set when USE_ASYNC_TASKS is True"
            )

        self.sqs = boto3.client("sqs", region_name=settings.AWS_SQS_REGION)
        self.queue_url = settings.AWS_SQS_QUEUE_URL
        self.dlq_url = getattr(settings, "AWS_SQS_DLQ_URL", None)

    def send_task(
        self,
        task_name: str,
        payload: dict[str, Any],
        delay_seconds: int = 0,
        message_group_id: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Send a task message to the SQS queue.

        Args:
            task_name: Name of the task to execute
            payload: Task payload data
            delay_seconds: Delay before message becomes available (0-900 seconds)
            message_group_id: Message group ID for FIFO queues

        Returns:
            SQS response dict or None if async tasks are disabled
        """
        if not settings.USE_ASYNC_TASKS:
            logger.info(f"Async tasks disabled. Would send task: {task_name}")
            return None

        message = {
            "task": task_name,
            "payload": payload,
            "timestamp": timezone.now().isoformat(),
            "source": "django-backend",
        }

        try:
            send_params = {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(message),
                "DelaySeconds": delay_seconds,
            }

            # Add message group ID for FIFO queues
            if message_group_id and self.queue_url.endswith(".fifo"):
                send_params["MessageGroupId"] = message_group_id
                send_params["MessageDeduplicationId"] = (
                    f"{task_name}-{timezone.now().timestamp()}"
                )

            response = self.sqs.send_message(**send_params)

            logger.info(
                f"Task '{task_name}' sent to SQS. MessageId: {response['MessageId']}"
            )

            return response

        except ClientError as e:
            logger.error(f"Failed to send task '{task_name}' to SQS: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending task '{task_name}': {e}")
            raise

    def send_guard_report_processing_task(
        self, report_id: int, **kwargs
    ) -> dict[str, Any] | None:
        """
        Send a guard report S3 processing task to the queue.

        Args:
            report_id: ID of the GuardReport to process
            **kwargs: Additional processing parameters

        Returns:
            SQS response or None
        """
        payload = {"report_id": report_id, **kwargs}
        return self.send_task("process_guard_report", payload)


# Global instance for easy access
sqs_client = SQSTaskClient()
