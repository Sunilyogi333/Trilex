import time
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def call_ai_service(params, retries=2, timeout=60):
    url = f"{settings.AI_SERVICE_URL}/query/"

    for attempt in range(retries + 1):
        try:
            response = requests.post(
                url,
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            logger.error(
                "AI service call failed (attempt %s/%s) url=%s params=%s",
                attempt + 1,
                retries + 1,
                url,
                params,
                exc_info=exc,
            )

            if attempt < retries:
                time.sleep(2)
                continue

            raise
