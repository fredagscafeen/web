from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_template_email(
    subject,
    body_template,
    to,
    text_format={},
    html_format={},
    cc=[],
    reply_to=[settings.BEST_MAIL],
):
    body_text = render_to_string(
        "email.txt", {"content": body_template.format(**text_format)}
    )
    body_html = render_to_string(
        "email.html", {"content": body_template.format(**html_format)}
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        to=to,
        cc=cc,
        reply_to=reply_to,
    )
    email.attach_alternative(body_html, "text/html")
    return email.send()
