from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

import httpx


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


async def create_payment_intent(
    *,
    base_url: str,
    event_id: int,
    fiat_amount: Decimal,
    fiat_currency: str = "ARS",
    kind: str = "ticket",
    preferred_provider: Optional[str] = None,
    telegram_user_id: Optional[int] = None,
    user_wallet: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_id": event_id,
        "kind": kind,
        "fiat_amount": str(fiat_amount),
        "fiat_currency": fiat_currency,
        "preferred_provider": preferred_provider,
        "telegram_user_id": telegram_user_id,
        "user_wallet": user_wallet,
        "metadata": metadata or {},
    }
    async with httpx.AsyncClient(base_url=_normalize_base_url(base_url), timeout=timeout) as client:
        response = await client.post("/api/payments/create", json=payload)
        response.raise_for_status()
        return response.json()


async def get_payment_status(
    *,
    base_url: str,
    payment_id: str,
    timeout: float = 20.0,
) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=_normalize_base_url(base_url), timeout=timeout) as client:
        response = await client.get(f"/api/payments/{payment_id}/status")
        response.raise_for_status()
        return response.json()
