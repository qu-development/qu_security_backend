from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """Custom storage for static files"""

    location = settings.AWS_LOCATION
    default_acl = None
    file_overwrite = False


class MediaStorage(S3Boto3Storage):
    """Custom storage for media files"""

    location = settings.AWS_MEDIA_LOCATION
    default_acl = None
    file_overwrite = False
