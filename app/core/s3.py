import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

MAX_FILE_SIZE = 5 * 1024 * 1024

_session: aioboto3.Session | None = None


def _get_session() -> aioboto3.Session:
    global _session
    if _session is None:
        _session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
    return _session


@asynccontextmanager
async def _get_client() -> AsyncGenerator:
    session = _get_session()
    async with session.client(
        "s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL
    ) as client:
        yield client


def _validate_file(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        allowed = ", ".join(ALLOWED_CONTENT_TYPES)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed}",
        )


async def _check_file_size(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_mb}MB",
        )
    return content


def _get_file_extension(content_type: str) -> str:
    extensions = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    return extensions.get(content_type, "jpg")


def _build_url(bucket_name: str, key: str) -> str:
    if settings.AWS_S3_ENDPOINT_URL:
        return f"{settings.AWS_S3_ENDPOINT_URL}/{bucket_name}/{key}"
    return f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


async def _ensure_bucket_exists(bucket_name: str) -> None:
    async with _get_client() as client:
        try:
            await client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    if settings.AWS_REGION == "us-east-1":
                        await client.create_bucket(Bucket=bucket_name)
                    else:
                        await client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={
                                "LocationConstraint": settings.AWS_REGION
                            },
                        )
                    logger.info(f"Created S3 bucket: {bucket_name}")
                except ClientError as create_error:
                    logger.error(
                        f"Failed to create bucket {bucket_name}: {create_error}"
                    )
                    raise
            else:
                raise


async def upload_file(bucket_name: str, file: UploadFile) -> str:
    _validate_file(file)
    content = await _check_file_size(file)

    extension = _get_file_extension(file.content_type or "image/jpeg")
    key = f"{uuid.uuid4()}.{extension}"

    await _ensure_bucket_exists(bucket_name)

    async with _get_client() as client:
        try:
            await client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=content,
                ContentType=file.content_type,
            )
            logger.info(f"Uploaded file to S3: {bucket_name}/{key}")
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file",
            ) from e

    return _build_url(bucket_name, key)


async def delete_file(bucket_name: str, file_url: str) -> bool:
    try:
        if settings.AWS_S3_ENDPOINT_URL and file_url.startswith(
            settings.AWS_S3_ENDPOINT_URL
        ):
            key = file_url.split(f"/{bucket_name}/")[-1]
        else:
            key = file_url.split("/")[-1]
    except (IndexError, AttributeError):
        logger.warning(f"Could not extract key from URL: {file_url}")
        return False

    async with _get_client() as client:
        try:
            await client.delete_object(Bucket=bucket_name, Key=key)
            logger.info(f"Deleted file from S3: {bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False


async def upload_category_image(file: UploadFile) -> str:
    return await upload_file(settings.AWS_S3_BUCKET_CATEGORIES, file)


async def upload_product_image(file: UploadFile) -> str:
    return await upload_file(settings.AWS_S3_BUCKET_PRODUCTS, file)


async def delete_category_image(file_url: str) -> bool:
    return await delete_file(settings.AWS_S3_BUCKET_CATEGORIES, file_url)


async def delete_product_image(file_url: str) -> bool:
    return await delete_file(settings.AWS_S3_BUCKET_PRODUCTS, file_url)
