import re

from django.db.models import TextField
from django.utils.translation import gettext_lazy as _

from .validators import validate_comma_separated_emails


def decode_db_comma_separated_emails(value: str) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        matches = re.findall(r"'(.*?)'", value)
        if matches:
            return matches
        return []
    raise ValueError(
        "Invalid value for 'decode_db_comma_separated_emails': expected a string or list of strings."
    )


def decode_input_comma_separated_emails(value: str) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value.strip() for value in value.split(",") if value.strip()]
    raise ValueError(
        "Invalid value for 'decode_input_comma_separated_emails': expected a string or list of strings."
    )


def encode_comma_separated_emails(value: list[str]) -> str:
    if isinstance(value, list):
        return str(value)
    if isinstance(value, str):
        return value
    raise ValueError(
        "Invalid value for 'encode_comma_separated_emails': expected a string or list of strings."
    )


class CommaSeparatedEmailField(TextField):
    default_validators = [validate_comma_separated_emails]
    description = _("Comma-separated emails")

    def __init__(self, *args, **kwargs):
        self.separator = ","
        self.default = "[]"
        kwargs["blank"] = True
        kwargs["default"] = self.default
        kwargs["help_text"] = _("Comma separated list of recipient emails")
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            "error_messages": {
                "invalid": _("Only comma separated emails are allowed."),
            }
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def from_db_value(self, value, expression, connection):
        return decode_db_comma_separated_emails(value)

    def get_prep_value(self, value):
        """
        We need to accomodate queries where a single email,
        or list of email addresses is supplied as arguments. For example:

        - OutgoingEmail.objects.filter(to='mail@example.com')
        - OutgoingEmail.objects.filter(to=['one@example.com', 'two@example.com'])
        """
        if value is None or value == "":
            value = self.default
        print(f"Preparing value for database: {value} (type: {type(value)})")
        return encode_comma_separated_emails(value)

    def to_python(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return decode_input_comma_separated_emails(value)
        raise ValueError(
            "Invalid value for CommaSeparatedEmailField: expected a string or list of strings."
        )
