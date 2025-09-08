# AWS SQS + Lambda Setup Guide

This guide covers the complete setup and deployment of the AWS SQS + Lambda asynchronous task processing system for the QU Security Backend.

## 🏗️ Architecture Overview

```
Django App → SQS Queue → Lambda Function → Task Processing
     ↓           ↓            ↓              ↓
   API Call → Message → Event Trigger → Email/File/Report
```

### Components:
- **Django Backend**: Sends tasks to SQS queues
- **SQS Queues**: Message queues for task distribution
- **Lambda Functions**: Process tasks asynchronously
- **Dead Letter Queues**: Handle failed messages
- **EventBridge**: Schedule periodic tasks (optional)

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Zappa** installed and configured
4. **IAM Role** with required permissions

## 🔧 AWS Infrastructure Setup

### 1. Create SQS Queues

#### Development Environment
```bash
# Main task queue
aws sqs create-queue \
  --queue-name qu-security-tasks-dev \
  --attributes '{
    "VisibilityTimeoutSeconds": "300",
    "MessageRetentionPeriod": "1209600",
    "ReceiveMessageWaitTimeSeconds": "20"
  }'

# Dead letter queue
aws sqs create-queue \
  --queue-name qu-security-tasks-dev-dlq \
  --attributes '{
    "MessageRetentionPeriod": "1209600"
  }'

# Configure DLQ redrive policy
aws sqs set-queue-attributes \
  --queue-url https://sqs.us-east-2.amazonaws.com/221082186476/qu-security-tasks-dev \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-2:221082186476:qu-security-tasks-dev-dlq\",\"maxReceiveCount\":3}"
  }'
```

#### Production Environment
```bash
# Main task queue
aws sqs create-queue \
  --queue-name qu-security-tasks-prod \
  --attributes '{
    "VisibilityTimeoutSeconds": "300",
    "MessageRetentionPeriod": "1209600",
    "ReceiveMessageWaitTimeSeconds": "20"
  }'

# Dead letter queue
aws sqs create-queue \
  --queue-name qu-security-tasks-prod-dlq \
  --attributes '{
    "MessageRetentionPeriod": "1209600"
  }'

# Configure DLQ redrive policy
aws sqs set-queue-attributes \
  --queue-url https://sqs.us-east-2.amazonaws.com/221082186476/qu-security-tasks-prod \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-2:221082186476:qu-security-tasks-prod-dlq\",\"maxReceiveCount\":3}"
  }'
```

### 2. IAM Role Permissions

Ensure your Lambda execution role has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:SendMessage"
      ],
      "Resource": [
        "arn:aws:sqs:us-east-2:221082186476:qu-security-tasks-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::qu-security-static/*",
        "arn:aws:s3:::qu-security-static-prod/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## 🚀 Deployment Steps

### 1. Deploy Django Backend

```bash
# Development
zappa deploy dev

# Production
zappa deploy production
```

### 2. Deploy Task Processor Lambda

```bash
# Development
zappa deploy task-processor-dev

# Production
zappa deploy task-processor-prod
```

### 3. Configure SQS Event Sources

The event sources are automatically configured via `zappa_settings.json`, but you can also set them up manually:

```bash
# Create event source mapping
aws lambda create-event-source-mapping \
  --function-name qu-security-task-processor \
  --event-source-arn arn:aws:sqs:us-east-2:221082186476:qu-security-tasks-dev \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5
```

## ⚙️ Configuration

### Environment Variables

#### Django Backend (.env or zappa_settings.json)
```bash
USE_ASYNC_TASKS=True
AWS_SQS_QUEUE_URL=https://sqs.us-east-2.amazonaws.com/221082186476/qu-security-tasks-dev
AWS_SQS_REGION=us-east-2
AWS_SQS_DLQ_URL=https://sqs.us-east-2.amazonaws.com/221082186476/qu-security-tasks-dev-dlq
```

#### Lambda Task Processor
```bash
USE_ASYNC_TASKS=False  # Lambda processes tasks synchronously
DEFAULT_FROM_EMAIL=noreply@qusecurity.com
```

### Django Settings

The following settings are automatically configured:

```python
# AWS SQS Configuration for Async Tasks
USE_ASYNC_TASKS = os.environ.get("USE_ASYNC_TASKS", "False").lower() == "true"
AWS_SQS_QUEUE_URL = os.environ.get("AWS_SQS_QUEUE_URL")
AWS_SQS_REGION = os.environ.get("AWS_SQS_REGION", "us-east-1")
AWS_SQS_DLQ_URL = os.environ.get("AWS_SQS_DLQ_URL")
```

## 📝 Usage Examples

### 1. Basic Async Task

```python
from common.tasks import send_notification_email

# This will send to SQS if USE_ASYNC_TASKS=True
# Otherwise executes synchronously
send_notification_email(
    user_id=123,
    subject="Welcome!",
    template_name="emails/welcome.html",
    context={"name": "John"}
)
```

### 2. GuardReport Processing

```python
from common.tasks import process_guard_report

# Automatically called when creating a GuardReport
# Handles file processing, thumbnails, and notifications
process_guard_report(report_id=456)
```

### 3. Direct SQS Usage

```python
from common.services.sqs_client import sqs_client

# Send custom task
sqs_client.send_task(
    task_name="custom_processing",
    payload={"data": "example"},
    delay_seconds=30
)
```

## 🔍 Monitoring and Debugging

### 1. CloudWatch Logs

Monitor Lambda execution:
```bash
# View logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/qu-security

# Tail logs
aws logs tail /aws/lambda/qu-security-task-processor --follow
```

### 2. SQS Monitoring

```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-2.amazonaws.com/221082186476/qu-security-tasks-dev \
  --attribute-names All

# Check DLQ for failed messages
aws sqs receive-message \
  --queue-url https://sqs.us-east-2.amazonaws.com/221082186476/qu-security-tasks-dev-dlq
```

### 3. Django Logging

Add to your Django settings for debugging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'common.tasks': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'common.services.sqs_client': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Tasks not processing**
   - Check SQS queue visibility timeout
   - Verify Lambda function permissions
   - Check CloudWatch logs for errors

2. **Messages going to DLQ**
   - Review Lambda function logs
   - Check message format
   - Verify database connectivity

3. **High costs**
   - Monitor Lambda execution time
   - Optimize batch sizes
   - Use reserved capacity if needed

### Error Handling

The system includes comprehensive error handling:

- **Retry Logic**: Failed messages are retried up to 3 times
- **Dead Letter Queue**: Permanently failed messages are moved to DLQ
- **Logging**: All errors are logged to CloudWatch
- **Graceful Degradation**: System falls back to synchronous processing

## 📊 Cost Optimization

### SQS Costs
- First 1M requests/month: **FREE**
- Additional requests: $0.40 per million

### Lambda Costs
- First 1M invocations/month: **FREE**
- First 400,000 GB-seconds/month: **FREE**
- Additional: $0.0000166667 per GB-second

### Optimization Tips
1. **Batch Processing**: Use batch sizes of 10 for SQS triggers
2. **Memory Allocation**: Start with 1024MB, adjust based on usage
3. **Timeout Settings**: Set appropriate timeouts (300s for task processor)
4. **Reserved Capacity**: Consider for predictable workloads

## 🔄 Updates and Maintenance

### Updating Lambda Functions

```bash
# Update Django backend
zappa update dev
zappa update production

# Update task processor
zappa update task-processor-dev
zappa update task-processor-prod
```

### Adding New Task Types

1. Add task handler to `lambda_functions/task_handlers.py`
2. Register in `lambda_functions/task_processor.py`
3. Create async task function in `common/tasks.py`
4. Deploy updates

### Scaling Considerations

- **Concurrent Executions**: Lambda automatically scales
- **SQS Throughput**: Standard queues support nearly unlimited TPS
- **Database Connections**: Monitor RDS connection limits
- **Memory Usage**: Adjust Lambda memory based on task complexity

## 🔐 Security Best Practices

1. **IAM Permissions**: Use least privilege principle
2. **VPC Configuration**: Deploy Lambda in VPC if needed
3. **Encryption**: Enable SQS message encryption
4. **Secrets Management**: Use AWS Secrets Manager for sensitive data
5. **Network Security**: Restrict access to necessary resources only

## 📈 Performance Metrics

Monitor these key metrics:

- **SQS Queue Depth**: Should remain low
- **Lambda Duration**: Optimize for cost and performance
- **Error Rate**: Should be < 1%
- **DLQ Messages**: Should be minimal
- **Database Connections**: Monitor connection pool usage

This setup provides a robust, scalable, and cost-effective asynchronous task processing system for your Django backend!
