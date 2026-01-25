from __future__ import annotations

import json
import logging
import re
from typing import Optional

import requests

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - playwright is optional
    sync_playwright = None


logger = logging.getLogger("link_utils")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://venti.com.ar/",
    "Platform": "web",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
}

CANONICAL_RE = re.compile(
    r'rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
LDJSON_URL_RE = re.compile(
    r'"@type"\s*:\s*"Event".*?"url"\s*:\s*"([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)

PLAYWRIGHT_AVAILABLE = sync_playwright is not None


def extract_canonical_html(html: str) -> Optional[str]:
    """Extract canonical link (or Event url from ld+json) from raw HTML."""
    if not html:
        return None
    m = CANONICAL_RE.search(html)
    if m:
        return m.group(1)
    m = LDJSON_URL_RE.search(html)
    if m:
        return m.group(1)
    return None


def extract_canonical_via_browser(url: str) -> Optional[str]:
    """Use Playwright (if available) to read canonical/link data."""
    if not PLAYWRIGHT_AVAILABLE or not url:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            canonical = page.eval_on_selector(
                "link[rel='canonical']",
                "el => el ? el.href : null",
            )
            if canonical:
                browser.close()
                return canonical
            ld_json = page.eval_on_selector(
                "script[type='application/ld+json']",
                "el => el ? el.textContent : null",
            )
            browser.close()
            if ld_json:
                try:
                    data = json.loads(ld_json)
                    if isinstance(data, dict):
                        url_value = data.get("url")
                        if url_value:
                            return url_value
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug("Failed to parse ld+json for %s: %s", url, exc)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Playwright canonical fetch failed for %s: %s", url, exc)
    return None


def resolve_canonical_url(
    url: str,
    session: Optional[requests.Session] = None,
    headers: Optional[dict] = None,
) -> str:
    """Return canonical URL for the provided link if possible."""
    if not url:
        return url

    req_headers = headers if headers is not None else DEFAULT_HEADERS
    fetch = session.get if session else requests.get  # type: ignore[assignment]

    try:
        resp = fetch(
            url,
            timeout=15,
            allow_redirects=True,
            headers=req_headers,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.debug("Failed to fetch %s for canonical resolution: %s", url, exc)
        return url

    canonical = extract_canonical_html(resp.text)
    if canonical:
        return canonical

    browser_canonical = extract_canonical_via_browser(resp.url or url)
    if browser_canonical:
        return browser_canonical

    return resp.url or url


__all__ = [
    "resolve_canonical_url",
    "extract_canonical_html",
    "extract_canonical_via_browser",
]
