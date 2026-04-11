import boto3
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .models import ForwardedMail

RETRYABLE_FORWARDED_STATUSES = {
    ForwardedMail.Status.FAILED,
    ForwardedMail.Status.BOUNCED,
}


def get_latest_forwarded_mails(incoming_mail):
    return incoming_mail.forward_attempts.filter(retry_attempts__isnull=True)


def get_retryable_forwarded_mails(incoming_mail):
    return get_latest_forwarded_mails(incoming_mail).filter(
        status__in=RETRYABLE_FORWARDED_STATUSES
    )


def build_mail_archive_download_url(mail_archive):
    if not settings.MAIL_ARCHIVE_BUCKET_NAME:
        raise ImproperlyConfigured("MAIL_ARCHIVE_BUCKET_NAME is not configured.")

    client = boto3.client("s3", region_name=settings.MAIL_ARCHIVE_AWS_REGION)
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.MAIL_ARCHIVE_BUCKET_NAME,
            "Key": mail_archive.s3_object_key,
        },
        ExpiresIn=settings.MAIL_ARCHIVE_PRESIGNED_URL_EXPIRATION,
    )


def request_forwarded_mail_resend(forwarded_mail):
    if forwarded_mail.status not in RETRYABLE_FORWARDED_STATUSES:
        raise ValueError("Only failed or bounced forwarded mail can be resent.")

    if not settings.DATMAIL_CONTROL_URL:
        raise ImproperlyConfigured("DATMAIL_CONTROL_URL is not configured.")

    response = requests.post(
        settings.DATMAIL_CONTROL_URL,
        json={
            "request_uuid": str(forwarded_mail.incoming_mail.mail_archive.request_uuid),
            "incoming_mail_id": forwarded_mail.incoming_mail_id,
            "forwarded_mail_id": forwarded_mail.pk,
            "target": forwarded_mail.target,
            "sender": forwarded_mail.incoming_mail.sender,
            "original_target": forwarded_mail.incoming_mail.target,
        },
        headers={
            "Authorization": f"Bearer {settings.DATMAIL_CONTROL_TOKEN}",
        },
        timeout=settings.DATMAIL_CONTROL_TIMEOUT,
    )
    response.raise_for_status()
    return response
