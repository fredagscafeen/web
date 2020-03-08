from django.db import models
from django.utils.crypto import get_random_string

EMAIL_TOKEN_LENGTH = 64


def get_new_email_token():
    return get_random_string(EMAIL_TOKEN_LENGTH)


class EmailToken(models.Model):
    email = models.EmailField(unique=True)
    token = models.CharField(max_length=EMAIL_TOKEN_LENGTH, default=get_new_email_token)

    def refresh_token(self):
        self.token = get_new_email_token()
        self.save()
