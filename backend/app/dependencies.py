import logging

import httpx
from fastapi import Header, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_SKIP_KEYS = {"", "1x0000000000000000000000000000000AA", "2x0000000000000000000000000000000AA"}


def verify_turnstile(cf_turnstile_response: str = Header(..., alias="CF-Turnstile-Response")) -> None:
    secret = settings.cloudflare_turnstile_secret_key
    if secret in _SKIP_KEYS:
        return  # dev mode / test key bypass

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                TURNSTILE_VERIFY_URL,
                data={"secret": secret, "response": cf_turnstile_response},
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="Turnstile verification service unavailable")
    except Exception as e:
        logger.error("Turnstile request error: %s", e)
        raise HTTPException(status_code=503, detail="Turnstile verification service error")

    if not result.get("success"):
        logger.warning("Turnstile failed: %s", result.get("error-codes"))
        raise HTTPException(status_code=403, detail="Turnstile verification failed")
