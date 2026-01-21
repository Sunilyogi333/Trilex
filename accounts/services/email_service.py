# import logging
# from django.template.loader import render_to_string

# from .brevo_email import send_email_brevo
# from .async_utils import run_async

# logger = logging.getLogger(__name__)


# def _send_templated_email(
#     *,
#     subject: str,
#     text_template: str,
#     html_template: str,
#     context: dict,
#     to_email: str,
# ):
#     """
#     Render templates and send email via Brevo.
#     """
#     try:
#         text_body = render_to_string(text_template, context)
#         html_body = render_to_string(html_template, context)

#         run_async(
#             send_email_brevo,
#             to_email=to_email,
#             subject=subject,
#             html_content=html_body,
#             text_content=text_body,
#         )

#     except Exception as e:
#         logger.exception(f"Email rendering failed: {e}")


# def send_signup_otp_email(email: str, otp: str) -> None:
#     _send_templated_email(
#         subject="Signup OTP Verification – Trilex",
#         text_template="emails/signup_otp.txt",
#         html_template="emails/signup_otp.html",
#         context={"email": email, "otp": otp},
#         to_email=email,
#     )


# def send_verification_link_email(email: str, verification_link: str) -> None:
#     _send_templated_email(
#         subject="Verify your email - Trilex",
#         text_template="emails/verify_email.txt",
#         html_template="emails/verify_email.html",
#         context={"email": email, "verification_link": verification_link},
#         to_email=email,
#     )


# def send_forgot_password_otp(email: str, otp: str) -> None:
#     _send_templated_email(
#         subject="Your Trilex OTP Code",
#         text_template="emails/otp_email.txt",
#         html_template="emails/otp_email.html",
#         context={"email": email, "otp": otp},
#         to_email=email,
#     )

import logging
from django.template.loader import render_to_string

from .brevo_email import send_email_brevo
from .async_utils import run_async

logger = logging.getLogger(__name__)


def _send_templated_email(
    *,
    subject: str,
    text_template: str,
    html_template: str,
    context: dict,
    to_email: str,
):
    """
    Render templates and send email via Brevo.
    """
    try:
        text_body = render_to_string(text_template, context)
        html_body = render_to_string(html_template, context)

        run_async(
            send_email_brevo,
            to_email=to_email,
            subject=subject,
            html_content=html_body,
            text_content=text_body,
        )

    except Exception as e:
        logger.exception(f"Email rendering failed: {e}")


def send_signup_otp_email(email: str, otp: str) -> None:
    _send_templated_email(
        subject="Signup OTP Verification – Trilex",
        text_template="emails/signup_otp.txt",
        html_template="emails/signup_otp.html",
        context={"email": email, "otp": otp},
        to_email=email,
    )


def send_verification_link_email(email: str, verification_link: str) -> None:
    _send_templated_email(
        subject="Verify your email - Trilex",
        text_template="emails/verify_email.txt",
        html_template="emails/verify_email.html",
        context={"email": email, "verification_link": verification_link},
        to_email=email,
    )


def send_forgot_password_otp(email: str, otp: str) -> None:
    _send_templated_email(
        subject="Your Trilex OTP Code",
        text_template="emails/otp_email.txt",
        html_template="emails/otp_email.html",
        context={"email": email, "otp": otp},
        to_email=email,
    )
