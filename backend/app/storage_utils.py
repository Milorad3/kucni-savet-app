import os
import boto3
from botocore.exceptions import ClientError

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION", "eu-central-1")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")  # opciono - za R2/B2, ostavi prazno za AWS S3

STORAGE_ENABLED = bool(S3_BUCKET_NAME and S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY)


def _get_client():
    kwargs = {
        "aws_access_key_id": S3_ACCESS_KEY_ID,
        "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
        "region_name": S3_REGION,
    }
    if S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def upload_file(file_bytes: bytes, key: str, content_type: str) -> bool:
    if not STORAGE_ENABLED:
        return False
    try:
        client = _get_client()
        client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=file_bytes, ContentType=content_type)
        return True
    except ClientError:
        return False


def get_download_url(key: str, expires_in: int = 3600) -> str:
    """Generise privremeni link za preuzimanje (presigned URL) - vazi ograniceno vreme."""
    if not STORAGE_ENABLED:
        return ""
    try:
        client = _get_client()
        return client.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET_NAME, "Key": key}, ExpiresIn=expires_in
        )
    except ClientError:
        return ""
