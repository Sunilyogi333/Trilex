from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_signup_otp_email(email: str, otp: str) -> None:
    """
    Send signup OTP email (HTML + plain text).
    """
    context = {
        "email": email,
        "otp": otp,
    }

    subject = "Signup OTP Verification – Trilex"

    text_body = render_to_string("emails/signup_otp.txt", context)
    html_body = render_to_string("emails/signup_otp.html", context)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_message.attach_alternative(html_body, "text/html")
    email_message.send(fail_silently=False)


def send_verification_link_email(email: str, verification_link: str) -> None:
    """
    Send email verification link.
    """
    context = {
        "email": email,
        "verification_link": verification_link,
    }

    subject = "Verify your email - Trilex"

    text_body = render_to_string("emails/verify_email.txt", context)
    html_body = render_to_string("emails/verify_email.html", context)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_message.attach_alternative(html_body, "text/html")
    email_message.send(fail_silently=False)


def send_forgot_password_otp(email: str, otp: str) -> None:
    """
    Send forgot-password OTP email.
    """
    context = {
        "email": email,
        "otp": otp,
    }

    subject = "Your Trilex OTP Code"

    text_body = render_to_string("emails/otp_email.txt", context)
    html_body = render_to_string("emails/otp_email.html", context)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_message.attach_alternative(html_body, "text/html")
    email_message.send(fail_silently=False)
