from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

import requests

from ..config import Config

logger = logging.getLogger(__name__)

API_ENDPOINT = "https://api.ocr.space/parse/image"
CACHE_DIR = Path("storage/ocr_cache")
DEFAULT_LANGUAGE = "eng"
LANGUAGE_FALLBACKS = ("eng", "spa")
TIMEOUT = 30


def _enabled() -> bool:
    return bool(Config.OCR_SPACE_API_KEY)


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _load_cache(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return payload.get("text") or ""
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to read OCR.Space cache %s: %s", path, exc)
        return None


def _save_cache(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(
                {"text": text, "created_at": __import__("datetime").datetime.utcnow().isoformat()},
                fh,
                ensure_ascii=False,
            )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to persist OCR.Space cache %s: %s", path, exc)


def _request(payload: dict, files: Optional[dict] = None) -> str:
    for language in LANGUAGE_FALLBACKS:
        payload["language"] = language
        try:
            response = requests.post(
                API_ENDPOINT,
                data=payload,
                files=files,
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("OCR.Space request failed: %s", exc)
            return ""

        if response.status_code == 403:
            logger.error("OCR.Space quota exceeded or key invalid (HTTP 403).")
            return ""

        try:
            data = response.json()
        except ValueError as exc:  # pragma: no cover
            logger.warning("OCR.Space JSON decode failed: %s", exc)
            return ""

        if data.get("IsErroredOnProcessing"):
            message = data.get("ErrorMessage") or data.get("ErrorDetails") or "unknown error"
            logger.warning("OCR.Space error (lang %s): %s", language, message)
            continue

        parsed_results = data.get("ParsedResults") or []
        texts = []
        for result in parsed_results:
            text = result.get("ParsedText")
            if text:
                texts.append(text.strip())
        if texts:
            return "\n".join(texts).strip()
    return ""


def extract_text(url: str) -> str:
    """Return text recognised by OCR.Space for a remote image URL."""
    if not _enabled() or not url:
        return ""

    cache_key = f"url:{url}"
    cache_file = _cache_path(cache_key)
    cached = _load_cache(cache_file)
    if cached is not None:
        return cached

    payload = {
        "apikey": Config.OCR_SPACE_API_KEY,
        "url": url,
        "OCREngine": 2,
        "isOverlayRequired": False,
    }
    text = _request(payload)
    if text:
        _save_cache(cache_file, text)
    return text


def extract_text_from_bytes(blob: bytes) -> str:
    """Return text recognised by OCR.Space for raw image bytes."""
    if not _enabled() or not blob:
        return ""

    digest = hashlib.sha256(blob).hexdigest()
    cache_key = f"bytes:{digest}"
    cache_file = _cache_path(cache_key)
    cached = _load_cache(cache_file)
    if cached is not None:
        return cached

    payload = {
        "apikey": Config.OCR_SPACE_API_KEY,
        "OCREngine": 2,
        "isOverlayRequired": False,
    }
    # Free tier supports multipart upload up to 1 MB. If больше - клиент должен ужать до отправки.
    files = {"file": ("image.jpg", blob)}
    text = _request(payload, files=files)
    if text:
        _save_cache(cache_file, text)
    return text
