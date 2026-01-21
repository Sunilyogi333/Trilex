from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _send_email(subject, text_template, html_template, context, to_email):
    try:
        text_body = render_to_string(text_template, context)
        html_body = render_to_string(html_template, context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send()

    except Exception as e:
        logger.error(f"Email API failed: {e}")


def send_signup_otp_email(email: str, otp: str) -> None:
    _send_email(
        subject="Signup OTP Verification – Trilex",
        text_template="emails/signup_otp.txt",
        html_template="emails/signup_otp.html",
        context={"email": email, "otp": otp},
        to_email=email,
    )


def send_verification_link_email(email: str, verification_link: str) -> None:
    _send_email(
        subject="Verify your email - Trilex",
        text_template="emails/verify_email.txt",
        html_template="emails/verify_email.html",
        context={"email": email, "verification_link": verification_link},
        to_email=email,
    )


def send_forgot_password_otp(email: str, otp: str) -> None:
    _send_email(
        subject="Your Trilex OTP Code",
        text_template="emails/otp_email.txt",
        html_template="emails/otp_email.html",
        context={"email": email, "otp": otp},
        to_email=email,
    )
