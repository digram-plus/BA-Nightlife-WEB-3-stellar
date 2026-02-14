import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


SUPPORTED_PAYMENT_PROVIDERS = ("moneygram", "airtm")
DEFAULT_PAYMENT_PROVIDER = "moneygram"


def choose_provider(preferred_provider: Optional[str]) -> str:
    if not preferred_provider:
        return DEFAULT_PAYMENT_PROVIDER
    candidate = preferred_provider.strip().lower()
    if candidate in SUPPORTED_PAYMENT_PROVIDERS:
        return candidate
    return DEFAULT_PAYMENT_PROVIDER


def _provider_base_url(provider: str) -> str:
    if provider == "moneygram":
        return os.getenv("PAYMENT_MONEYGRAM_CHECKOUT_URL", "https://moneygram.com/intl/stellarwallets")
    if provider == "airtm":
        return os.getenv("PAYMENT_AIRTM_CHECKOUT_URL", "https://airtm.com/")
    raise ValueError(f"Unsupported provider: {provider}")


def build_checkout_url(provider: str, payment_id: str) -> str:
    """
    Generates a user-facing URL for checkout.
    """
    base_url = _provider_base_url(provider)
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("reference", payment_id)
    query.setdefault("source", "ba-nightlife-bot")
    encoded_query = urlencode(query)
    return urlunparse(parsed._replace(query=encoded_query))


def get_webhook_secret(provider: str) -> Optional[str]:
    if provider == "moneygram":
        return os.getenv("PAYMENT_MONEYGRAM_WEBHOOK_SECRET")
    if provider == "airtm":
        return os.getenv("PAYMENT_AIRTM_WEBHOOK_SECRET")
    return None


def normalize_payment_status(raw_status: Optional[str]) -> str:
    if not raw_status:
        return "processing"
    status = raw_status.strip().lower()
    if any(token in status for token in ("complete", "success", "settled", "paid")):
        return "completed"
    if any(token in status for token in ("cancel",)):
        return "cancelled"
    if any(token in status for token in ("expire", "timeout")):
        return "expired"
    if any(token in status for token in ("fail", "error", "reject", "declin")):
        return "failed"
    if any(token in status for token in ("pending", "processing", "in_progress", "in-progress")):
        return "processing"
    return "processing"


def extract_payment_reference(payload: dict[str, Any]) -> Optional[str]:
    direct_keys = (
        "payment_id",
        "reference",
        "external_reference",
        "merchant_reference",
        "merchantReference",
    )
    for key in direct_keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("payment_id") or metadata.get("reference")
        if isinstance(value, str) and value.strip():
            return value.strip()

    data = payload.get("data")
    if isinstance(data, dict):
        nested = extract_payment_reference(data)
        if nested:
            return nested

    return None


def extract_provider_session_id(payload: dict[str, Any]) -> Optional[str]:
    keys = ("provider_session_id", "session_id", "sessionId", "transaction_id", "transactionId", "id")
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
