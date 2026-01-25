from __future__ import annotations

from datetime import date, time
from typing import Iterable
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..config import Config
from ..models import Event


GENRE_HOOKS: dict[str, str] = {
    "trance": "Субботний uplifting сет и море света.",
    "dnb": "Ломанные ритмы и массивный бас.",
    "house": "Лёгкий грув и много танцев.",
    "techno": "Гипнотический драйв до самого утра.",
}


def _format_time(ev_time: time | None) -> str:
    return ev_time.strftime("%H:%M") if ev_time else ""


def _format_genres(genres: Iterable[str] | None) -> str:
    if not genres:
        return ""
    tags = []
    for g in genres:
        g_key = (g or "MISC").upper()
        if g_key == "MISC":
            g_key = "GENERAL"
        tags.append(f"#{g_key}")
    return " ".join(tags)


def _pick_hook(genres: Iterable[str] | None) -> str:
    for g in (genres or []):
        hook = GENRE_HOOKS.get(g.lower())
        if hook:
            return hook
    return "Бери друзей и залетай — будет жарко!"


def build_caption(ev: Event) -> str:
    event_date: date | None = getattr(ev, "date", None)
    event_time: time | None = getattr(ev, "time", None)
    genres = getattr(ev, "genres", None)

    lines: list[str] = [f"🎵 {ev.title}"]

    parts_location: list[str] = []
    venue = getattr(ev, "venue_address", None) or getattr(ev, "venue", None)
    if venue:
        parts_location.append(venue)
        city = getattr(ev, "city", None)
        if city:
            parts_location.append(city)
    if parts_location:
        lines.append(f"📍 {', '.join(parts_location)}")

    if event_date or event_time:
        date_str = event_date.strftime("%d %B %Y") if event_date else ""
        time_str = ""
        if event_time and not (event_time.hour == 0 and event_time.minute == 0):
            time_str = _format_time(event_time)
        line = " ".join(part for part in (date_str, time_str) if part).strip()
        if line:
            lines.append(f"🗓 {line}")

    hook = getattr(ev, "hook", None) or getattr(ev, "description", None)
    if hook:
        lines.append(f"🎶 {hook}")
    else:
        default_hook = _pick_hook(genres)
        if default_hook:
            lines.append(f"🎶 {default_hook}")

    tags = _format_genres(genres)
    if tags:
        lines.append(tags)

    return "\n".join(lines)


def build_keyboard(ev: Event) -> InlineKeyboardMarkup:
    listen_url = getattr(ev, "artist_listen_url", None)
    if not listen_url:
        query = getattr(ev, "artist", None) or getattr(ev, "title", "")
        listen_url = f"{Config.DEFAULT_LISTEN_BASE}{quote_plus(query)}"

    buttons = [InlineKeyboardButton(text="🎧 Послушать", url=listen_url)]

    ticket_url = getattr(ev, "ticket_url", None)
    button_label = "🎟 Купить билет"
    if not ticket_url:
        ticket_url = getattr(ev, "source_link", None) or getattr(ev, "source_url", None)
        button_label = "ℹ️ Подробнее"

    if ticket_url:
        buttons.append(InlineKeyboardButton(text=button_label, url=ticket_url))
    elif Config.DEFAULT_INFO_URL:
        buttons.append(InlineKeyboardButton(text="ℹ️ Подробнее", url=Config.DEFAULT_INFO_URL))

    return InlineKeyboardMarkup(inline_keyboard=[buttons])
