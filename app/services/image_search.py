from __future__ import annotations

import os
import random
import time
from typing import Iterable, List

import requests

from ..config import Config

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


class ImageSearchError(Exception):
    """Raised when image search fails."""


def search_images(query: str, *, num: int = 5) -> List[str]:
    """Return a list of image URLs for the given query using Google Custom Search."""
    api_key = Config.GOOGLE_SEARCH_API_KEY
    cx = Config.GOOGLE_SEARCH_CX
    if not api_key or not cx:
        return []

    params = {
        "q": query,
        "searchType": "image",
        "num": num,
        "imgSize": "large",
        "imgType": "photo",
        "safe": "off",
        "key": api_key,
        "cx": cx,
    }

    try:
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    items = data.get("items") or []
    urls = []
    for it in items:
        link = it.get("link")
        if link:
            urls.append(link)
    return urls
