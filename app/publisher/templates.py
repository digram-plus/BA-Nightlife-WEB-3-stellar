import html
import random
from datetime import date, time
from typing import Iterable, Optional, Union
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..config import Config
from ..models import Event

GENRE_HOOKS: dict[str, list[str]] = {
    "trance": [
        "Погружайся в атмосферу транса и мелодичных ритмов.",
        "Субботний uplifting сет и море света.",
        "Транс-путешествие, которое нельзя пропустить.",
        "Магия транса перенесёт тебя в другое измерение."
    ],
    "dnb": [
        "Ломанные ритмы и массивный бас.",
        "Энергия драм-н-бейса до самого утра.",
        "Готовься к мощному саунду и ломанному биту.",
        "Для настоящих любителей баса и скорости."
    ],
    "house": [
        "Лёгкий грув и много танцев.",
        "Хаус-вайб для твоего идеального вечера.",
        "Классические ритмы и современный саунд.",
        "Танцуй под лучшие хаус-треки города."
    ],
    "techno": [
        "Гипнотический драйв до самого утра.",
        "Тёмный и мощный техно-ритм.",
        "Для тех, кто любит пожёстче и погромче.",
        "Погрузись в индустриальную эстетику ночи."
    ],
    "rock": [
        "Живой звук и драйв рок-сцены.",
        "Для фанатов гитарного соло и мощного вокала.",
        "Рок-вечер, который разбудит твою энергию.",
        "Настоящий дух свободы и живой музыки."
    ],
    "pop": [
        "Главные хиты и яркое шоу.",
        "Танцуй под любимые мелодии этого года.",
        "Поп-вечеринка с незабываемой атмосферо.",
        "Позитив, музыка и яркий свет."
    ],
    "rap": [
        "Ритм улиц и топовый флоу.",
        "Хип-хоп вайб и правильный кач.",
        "Лучшие биты и читка до самого рассвета.",
        "Urban style и музыка, которая качает."
    ],
    "general": [
        "Бери друзей и залетай — будет жарко!",
        "Не пропусти это событие — обещает быть круто.",
        "Отличный повод выбраться и круто провести время.",
        "Музыка, общение и море эмоций.",
        "Будь в центре событий этой ночи!"
    ]
}


def _format_time(ev_time: Optional[time]) -> str:
    return ev_time.strftime("%H:%M") if ev_time else ""


def _format_genres(genres: Optional[Iterable[str]]) -> str:
    if not genres:
        return ""
    tags = []
    for g in genres:
        g_key = (g or "MISC").upper()
        if g_key == "MISC":
            g_key = "GENERAL"
        tags.append(f"#{g_key}")
    return " ".join(tags)


def _pick_hook(genres: Optional[Iterable[str]]) -> str:
    for g in (genres or []):
        hooks = GENRE_HOOKS.get(g.lower())
        if hooks:
            return random.choice(hooks)
    return random.choice(GENRE_HOOKS["general"])


def _format_date_ru(d: date) -> str:
    months = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{d.day} {months[d.month]}"


def build_caption(ev: Event) -> str:
    event_date: Optional[date] = getattr(ev, "date", None)
    event_time: Optional[time] = getattr(ev, "time", None)
    genres = getattr(ev, "genres", None)

    # 1. Title
    # Escape title for HTML parse_mode
    safe_title = html.escape(ev.title or "")
    lines: list[str] = [f"<b>🎵 {safe_title}</b>"]

    # 2. Location with Google Maps link
    venue = getattr(ev, "venue_address", None) or getattr(ev, "venue", None)
    if venue:
        venue_query = quote_plus(venue)
        maps_url = f"https://www.google.com/maps/search/?api=1&query={venue_query}"
        safe_venue = html.escape(venue)
        lines.append(f"📍 <a href='{maps_url}'>{safe_venue}</a>")

    # 3. Date & Time
    if event_date:
        date_str = _format_date_ru(event_date)
        time_str = ""
        if event_time and not (event_time.hour == 0 and event_time.minute == 0):
            time_str = f" в {_format_time(event_time)}"
        lines.append(f"🗓 {date_str}{time_str}")

    # 4. Other information (Hook/Description)
    hook = getattr(ev, "hook", None) or getattr(ev, "description", None)
    if not hook:
        hook = _pick_hook(genres)
    
    if hook:
        safe_hook = html.escape(hook)
        lines.append(f"🎶 {safe_hook}")

    # 5. Hashtags
    tags = _format_genres(genres)
    if tags:
        lines.append(f"\n{tags}")

    return "\n".join(lines)


def build_keyboard(ev: Event) -> InlineKeyboardMarkup:
    buttons = []
    
    listen_url = getattr(ev, "artist_listen_url", None)
    artists = getattr(ev, "artists", None)
    
    if listen_url or artists:
        if not listen_url:
            query = " ".join(artists)
            listen_url = f"{Config.DEFAULT_LISTEN_BASE}{quote_plus(query)}"
        buttons.append(InlineKeyboardButton(text="🎧 Послушать", url=listen_url))

    ticket_url = getattr(ev, "ticket_url", None)
    button_label = "🎟 Купить билет"
    if not ticket_url:
        ticket_url = getattr(ev, "source_link", None) or getattr(ev, "source_url", None)
        button_label = "ℹ️ Подробнее"

    if ticket_url:
        buttons.append(InlineKeyboardButton(text=button_label, url=ticket_url))

    if not buttons:
        return None
        
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
