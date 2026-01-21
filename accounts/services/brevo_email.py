import os
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)


def send_email_brevo(
    *,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = "",
):
    """
    Send email using Brevo Transactional Email API.
    """
    try:
        api_key = os.getenv("BREVO_API_KEY")
        if not api_key:
            raise RuntimeError("BREVO_API_KEY not set")

        config = sib_api_v3_sdk.Configuration()
        config.api_key["api-key"] = api_key

        api = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(config)
        )

        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={
                "email": "trilex.testing@gmail.com",  # must be verified in Brevo
                "name": "Trilex",
            },
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

        response = api.send_transac_email(email)
        logger.info(f"Brevo email sent to {to_email}, messageId={response.message_id}")

        return response

    except ApiException as e:
        logger.error(f"Brevo API error: {e}")
    except Exception as e:
        logger.exception(f"Brevo email failed: {e}")
