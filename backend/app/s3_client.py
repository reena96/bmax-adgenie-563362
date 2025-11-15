"""
AWS S3 client for file storage and retrieval.
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from pathlib import Path

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# S3 client instance
s3_client = None


def get_s3_client():
    """
    Get or create S3 client instance.

    Returns:
        boto3 S3 client
    """
    global s3_client

    if s3_client is None:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        logger.info("S3 client initialized")

    return s3_client


def upload_to_s3(file_path: str, s3_key: str, content_type: Optional[str] = None) -> str:
    """
    Upload a file to S3.

    Args:
        file_path: Local file path to upload
        s3_key: S3 key (path) where file will be stored
        content_type: Optional MIME type for the file

    Returns:
        S3 URL of the uploaded file

    Raises:
        Exception if upload fails
    """
    try:
        client = get_s3_client()

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        client.upload_file(
            file_path,
            settings.AWS_S3_BUCKET,
            s3_key,
            ExtraArgs=extra_args if extra_args else None
        )

        s3_url = f"s3://{settings.AWS_S3_BUCKET}/{s3_key}"
        logger.info(f"File uploaded to S3: {s3_url}")
        return s3_url

    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise


def get_signed_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """
    Generate a presigned URL for downloading a file from S3.

    Args:
        s3_key: S3 key (path) of the file
        expiry_seconds: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL string

    Raises:
        Exception if URL generation fails
    """
    try:
        client = get_s3_client()

        url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET,
                'Key': s3_key
            },
            ExpiresIn=expiry_seconds
        )

        logger.info(f"Generated signed URL for {s3_key} (expires in {expiry_seconds}s)")
        return url

    except ClientError as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise


def object_exists(s3_key: str) -> bool:
    """
    Check if an object exists in S3.

    Args:
        s3_key: S3 key (path) to check

    Returns:
        True if object exists, False otherwise
    """
    try:
        client = get_s3_client()
        client.head_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logger.error(f"Error checking object existence: {e}")
            raise


def delete_object(s3_key: str) -> bool:
    """
    Delete an object from S3.

    Args:
        s3_key: S3 key (path) to delete

    Returns:
        True if deletion successful, False otherwise
    """
    try:
        client = get_s3_client()
        client.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
        logger.info(f"Deleted object from S3: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to delete object: {e}")
        return False


def list_objects(s3_prefix: str) -> list[str]:
    """
    List objects in S3 with a given prefix.

    Args:
        s3_prefix: S3 prefix (folder path) to list

    Returns:
        List of S3 keys matching the prefix
    """
    try:
        client = get_s3_client()
        response = client.list_objects_v2(
            Bucket=settings.AWS_S3_BUCKET,
            Prefix=s3_prefix
        )

        if 'Contents' not in response:
            return []

        keys = [obj['Key'] for obj in response['Contents']]
        logger.info(f"Listed {len(keys)} objects with prefix: {s3_prefix}")
        return keys

    except ClientError as e:
        logger.error(f"Failed to list objects: {e}")
        return []


def create_folder_structure():
    """
    Create the S3 folder structure by uploading empty marker files.
    S3 doesn't have real folders, but we can create the appearance of them.
    """
    folders = [
        "generated-videos/",
        "product-images/",
        "brand-assets/",
        "scene-videos/",
        "audio/"
    ]

    client = get_s3_client()

    for folder in folders:
        try:
            # Upload empty object to create folder
            client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=folder,
                Body=b''
            )
            logger.info(f"Created S3 folder: {folder}")
        except ClientError as e:
            logger.warning(f"Could not create folder {folder}: {e}")
