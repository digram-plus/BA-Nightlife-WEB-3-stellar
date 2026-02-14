from app.services.payments import (
    build_checkout_url,
    choose_provider,
    extract_payment_reference,
    extract_provider_session_id,
    normalize_payment_status,
)


def test_choose_provider_defaults_to_moneygram() -> None:
    assert choose_provider(None) == "moneygram"
    assert choose_provider("unknown") == "moneygram"
    assert choose_provider("airtm") == "airtm"


def test_build_checkout_url_includes_reference_and_source(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_MONEYGRAM_CHECKOUT_URL", "https://example.com/checkout")
    url = build_checkout_url("moneygram", "abc123")
    assert "reference=abc123" in url
    assert "source=ba-nightlife-bot" in url


def test_build_checkout_url_preserves_existing_query(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_AIRTM_CHECKOUT_URL", "https://airtm.example/pay?channel=tg")
    url = build_checkout_url("airtm", "ref42")
    assert "channel=tg" in url
    assert "reference=ref42" in url


def test_normalize_payment_status() -> None:
    assert normalize_payment_status("completed") == "completed"
    assert normalize_payment_status("paid_success") == "completed"
    assert normalize_payment_status("pending_kyc") == "processing"
    assert normalize_payment_status("user_cancelled") == "cancelled"
    assert normalize_payment_status("expired") == "expired"
    assert normalize_payment_status("failed") == "failed"
    assert normalize_payment_status(None) == "processing"


def test_extract_payment_reference_from_payload_variants() -> None:
    assert extract_payment_reference({"payment_id": "p1"}) == "p1"
    assert extract_payment_reference({"reference": "p2"}) == "p2"
    assert extract_payment_reference({"metadata": {"reference": "p3"}}) == "p3"
    assert extract_payment_reference({"data": {"external_reference": "p4"}}) == "p4"
    assert extract_payment_reference({"data": {"metadata": {"payment_id": "p5"}}}) == "p5"
    assert extract_payment_reference({"data": {"id": "ignored"}}) is None


def test_extract_provider_session_id() -> None:
    assert extract_provider_session_id({"session_id": "s1"}) == "s1"
    assert extract_provider_session_id({"transaction_id": "tx1"}) == "tx1"
    assert extract_provider_session_id({"id": "obj1"}) == "obj1"
    assert extract_provider_session_id({"status": "pending"}) is None
