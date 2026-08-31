import uuid

import boto3
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def upload_expense_attachment(uploaded_file, expense_item):
    if not settings.EXPENSE_ATTACHMENT_BUCKET_NAME:
        if settings.DEBUG:
            print(
                "Warning: EXPENSE_ATTACHMENT_BUCKET_NAME is not configured. Skipping upload to S3."
            )
            return f"local/{uuid.uuid4().hex}-{uploaded_file.name}"
        else:
            raise ImproperlyConfigured(
                "EXPENSE_ATTACHMENT_BUCKET_NAME is not configured."
            )

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION_NAME,
    )
    object_key = f"expense-attachments/{expense_item.expense_id}/{expense_item.id}/{uuid.uuid4().hex}-{uploaded_file.name}"

    client.put_object(
        Bucket=settings.EXPENSE_ATTACHMENT_BUCKET_NAME,
        Key=object_key,
        Body=uploaded_file.read(),
        ContentType=uploaded_file.content_type or "application/octet-stream",
    )

    return object_key


def build_expense_attachment_download_url(attachment):
    if not settings.EXPENSE_ATTACHMENT_BUCKET_NAME:
        raise ImproperlyConfigured("EXPENSE_ATTACHMENT_BUCKET_NAME is not configured.")

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION_NAME,
    )
    filename = attachment.s3_object_key.rsplit("/", 1)[-1]
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.EXPENSE_ATTACHMENT_BUCKET_NAME,
            "Key": attachment.s3_object_key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        },
        ExpiresIn=settings.EXPENSE_ATTACHMENT_PRESIGNED_URL_EXPIRATION,
    )
