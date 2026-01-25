from __future__ import annotations

import logging
import os
from functools import lru_cache
from io import BytesIO
from typing import List, Optional

import requests

from .ocr_space import (
    extract_text as extract_text_remote,
    extract_text_from_bytes as extract_text_remote_bytes,
)

_EASY_AVAILABLE = False
if os.getenv("DISABLE_EASYOCR") not in {"1", "true", "TRUE"}:
    try:
        import easyocr  # type: ignore
        import numpy as np
        from PIL import Image

        _EASY_AVAILABLE = True
    except Exception:  # pragma: no cover
        logging.warning("EasyOCR not available; OCR features disabled")
        _EASY_AVAILABLE = False
else:  # pragma: no cover
    logging.info("EasyOCR disabled via DISABLE_EASYOCR env var")

LANGUAGE_GROUPS = [
    ("latin", ["en", "es"]),
    ("cyrillic", ["en", "ru"]),
]

_readers: dict[str, Optional["easyocr.Reader"]] = {}


def _get_readers() -> List["easyocr.Reader"]:
    readers: List["easyocr.Reader"] = []
    if not _EASY_AVAILABLE:
        return readers

    for key, languages in LANGUAGE_GROUPS:
        reader = _readers.get(key)
        if reader is False:
            continue
        if reader is None:
            try:
                reader = easyocr.Reader(languages, gpu=False)
            except Exception as exc:  # pragma: no cover
                logging.warning(
                    "Failed to initialize EasyOCR (%s): %s", ",".join(languages), exc
                )
                _readers[key] = False
                continue
            _readers[key] = reader
        if reader:
            readers.append(reader)
    return readers


def _run_ocr(image_bytes: bytes) -> str:
    readers = _get_readers()
    if not readers or not image_bytes:
        return ""
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        arr = np.array(image)
    except Exception as exc:  # pragma: no cover
        logging.warning("OCR image decode failed: %s", exc)
        return ""

    texts: List[str] = []
    for reader in readers:
        try:
            result = reader.readtext(arr, detail=0, paragraph=True)
            if result:
                texts.append(" ".join(result))
        except Exception as exc:  # pragma: no cover
            logging.warning("OCR failed (%s): %s", reader.lang_list, exc)
    return " ".join(texts)


@lru_cache(maxsize=128)
def extract_text(url: str) -> str:
    """Return OCR text extracted from the image URL."""
    if not url:
        return ""
    remote_text = extract_text_remote(url)
    if remote_text:
        return remote_text

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return _run_ocr(resp.content)
    except Exception as exc:
        logging.warning("OCR failed for %s: %s", url, exc)
        return ""


def extract_text_from_bytes(data: bytes) -> str:
    """Return OCR text extracted from raw image bytes."""
    remote_text = extract_text_remote_bytes(data)
    if remote_text:
        return remote_text
    return _run_ocr(data)
