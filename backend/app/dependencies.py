import logging

import httpx
from fastapi import Depends, Header, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token

logger = logging.getLogger(__name__)
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_SKIP_KEYS = {"", "1x0000000000000000000000000000000AA", "2x0000000000000000000000000000000AA"}


def verify_turnstile(cf_turnstile_response: str | None = Header(None, alias="CF-Turnstile-Response")) -> None:
    secret = settings.cloudflare_turnstile_secret_key
    if secret in _SKIP_KEYS:
        return  # dev mode / test key bypass
    if not cf_turnstile_response:
        raise HTTPException(status_code=403, detail="Turnstile token required")

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


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user
