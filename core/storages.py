import boto3
from botocore.exceptions import ClientError
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
    default_acl = None  # ACLs are disabled on this bucket
    file_overwrite = False
    querystring_auth = True  # Use signed URLs for access

    def get_signed_url(self, name, expiration=3600):
        """
        Generate a signed URL for accessing a file.

        Args:
            name: The file name/key in S3
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL string or None if error
        """
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            # Generate the full S3 key including location prefix
            s3_key = f"{self.location}/{name}" if self.location else name

            signed_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return signed_url
        except ClientError as e:
            print(f"Error generating signed URL: {e}")
            return None
