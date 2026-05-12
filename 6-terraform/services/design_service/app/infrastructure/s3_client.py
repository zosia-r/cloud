import boto3
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "cukiernia-designs-zr")


def get_s3_client():
    logger.info("Tworzenie klienta S3")
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
    )


async def upload_file_to_s3(file_content: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
    """
    Uploaduje plik do S3.
    Zwraca s3_key (ścieżkę pliku w buckecie).
    """
    logger.info(f"upload_file_to_s3: uploading key={s3_key}, bucket={S3_BUCKET_NAME}, size={len(file_content)} bytes")
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
        )
        logger.info(f"upload_file_to_s3: plik zapisany w S3 pod kluczem {s3_key}")
        return s3_key
    except ClientError as e:
        logger.error(f"upload_file_to_s3: błąd S3: {e}")
        raise


async def generate_presigned_url(s3_key: str, expiration_seconds: int = 3600) -> str:
    """
    Generuje tymczasowy URL do pobrania pliku z S3.
    Domyślnie ważny 1 godzinę.
    """
    logger.info(f"generate_presigned_url: generuję URL dla key={s3_key}, expiration={expiration_seconds}s")
    try:
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expiration_seconds,
        )
        logger.info(f"generate_presigned_url: URL wygenerowany dla key={s3_key}")
        return url
    except ClientError as e:
        logger.error(f"generate_presigned_url: błąd S3: {e}")
        raise
