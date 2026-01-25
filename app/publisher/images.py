from __future__ import annotations

import asyncio
import ssl
from io import BytesIO
from pathlib import Path
from typing import Optional

import aiohttp
import certifi
from aiogram.types import BufferedInputFile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ..models import Event
from ..services.image_search import search_images

FONT_PRIMARY = Path("assets/Inter-SemiBold.ttf")
FONT_SECONDARY = Path("assets/Inter-Medium.ttf")

CANVAS_WIDTH = 1038
CANVAS_HEIGHT = 1368
OUTER_MARGIN = 48
INNER_MARGIN = 48
RADIUS = 18

BACKGROUND_TOP = "#100E10"
BACKGROUND_BOTTOM = "#1B0B17"
CONTAINER_COLOR = "#2E1115"
BORDER_COLOR = "#862D31"
FRAME_DARK = "#101010"
FRAME_LIGHT = "#141414"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#F8F2EF"

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"
    )
}

MAX_TELEGRAM_DIM = 2000
MIN_TELEGRAM_DIM = 20
ALLOWED_IMAGE_CT = {"image/jpeg", "image/png", "image/webp"}


async def get_event_media(ev: Event) -> Optional[BufferedInputFile]:
    """Return оригинальную афишу, если она есть, иначе сгенерированную карточку."""
    media_url = getattr(ev, "media_url", None)
    if media_url:
        original = await _download_image(media_url)
        if original:
            return BufferedInputFile(original, filename="event.jpg")

    portrait = await _get_event_portrait(ev)
    generated = _render_event_card(ev, portrait)
    if generated:
        return BufferedInputFile(generated, filename="event.png")
    return None


async def _download_image(url: str) -> Optional[bytes]:
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS) as session:
            async with session.get(url, ssl=SSL_CONTEXT) as resp:
                if resp.status != 200:
                    return None
                ctype = resp.headers.get("Content-Type", "") or ""
                raw = await resp.read()
                return _sanitize_image(raw, ctype)
    except Exception:
        return None


def _sanitize_image(raw: bytes, ctype: str) -> Optional[bytes]:
    # Если это не изображение, отдаём None
    if ctype and not any(ct in ctype for ct in ALLOWED_IMAGE_CT):
        return None
    try:
        image = Image.open(BytesIO(raw))
        image.load()
    except Exception:
        return None

    w, h = image.size
    if w < MIN_TELEGRAM_DIM or h < MIN_TELEGRAM_DIM:
        return None

    # Ограничиваем максимальный размер, чтобы Telegram не ругался
    scale = min(1.0, MAX_TELEGRAM_DIM / max(w, h))
    if scale < 1.0:
        new_size = (int(w * scale), int(h * scale))
        image = image.resize(new_size, Image.LANCZOS)

    # Конвертируем в RGB и сохраняем компактно
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    if image.mode == "RGBA":
        image = image.convert("RGB")

    buf = BytesIO()
    image.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()


async def _get_event_portrait(ev: Event) -> Optional[bytes]:
    queries: list[str] = []
    artist = getattr(ev, "artist", None)
    title = getattr(ev, "title", None)
    if artist:
        queries.append(artist)
        queries.append(f"{artist} live poster")
    if title:
        if not artist or artist.lower() not in title.lower():
            queries.append(title)
        queries.append(f"{title} poster")

    for query in queries:
        if not query:
            continue
        urls = await asyncio.to_thread(search_images, query)
        for url in urls:
            raw = await _download_image(url)
            if raw:
                return raw
    return None


def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _draw_rounded_rect(
    image: Image.Image,
    rect: tuple[int, int, int, int],
    radius: int,
    *,
    fill: Optional[str] = None,
    outline: Optional[str] = None,
    width: int = 1,
) -> None:
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)


def _apply_shadow(
    base: Image.Image,
    rect: tuple[int, int, int, int],
    radius: int,
    *,
    blur: int,
    spread: int,
    color: str,
    opacity: float,
) -> None:
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    r, g, b = _hex_to_rgb(color)
    alpha = int(255 * max(0, min(opacity, 1.0)))
    x0, y0, x1, y1 = rect
    inflated = (x0 - spread, y0 - spread, x1 + spread, y1 + spread)
    draw.rounded_rectangle(inflated, radius=radius + spread, fill=(r, g, b, alpha))
    blurred = shadow.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(blurred)


def _inset(rect: tuple[int, int, int, int], amount: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (x0 + amount, y0 + amount, x1 - amount, y1 - amount)


def _render_event_card(ev: Event, portrait_png: Optional[bytes]) -> Optional[bytes]:
    base = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT))
    draw = ImageDraw.Draw(base)

    top_rgb = _hex_to_rgb(BACKGROUND_TOP)
    bottom_rgb = _hex_to_rgb(BACKGROUND_BOTTOM)
    for y in range(CANVAS_HEIGHT):
        ratio = y / max(CANVAS_HEIGHT - 1, 1)
        r = int(top_rgb[0] * (1 - ratio) + bottom_rgb[0] * ratio)
        g = int(top_rgb[1] * (1 - ratio) + bottom_rgb[1] * ratio)
        b = int(top_rgb[2] * (1 - ratio) + bottom_rgb[2] * ratio)
        draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(r, g, b))

    genre_font = _load_font(FONT_PRIMARY, 96)
    artist_font = _load_font(FONT_SECONDARY, 60)
    body_font = _load_font(FONT_SECONDARY, 42)

    genre_text = ((getattr(ev, "genres", None) or ["MISC"])[0] or "MISC").upper()
    draw.text((OUTER_MARGIN, OUTER_MARGIN), genre_text, font=genre_font, fill=TEXT_PRIMARY)
    genre_height = genre_font.getbbox(genre_text)[3]

    artist_text = getattr(ev, "artist", None) or ev.title
    artist_bbox = artist_font.getbbox(artist_text)
    artist_width = artist_bbox[2]
    artist_height = artist_bbox[3]
    artist_x = CANVAS_WIDTH - OUTER_MARGIN - artist_width
    artist_y = OUTER_MARGIN + max(0, (genre_height - artist_height) // 2)
    draw.text((artist_x, artist_y), artist_text, font=artist_font, fill=TEXT_PRIMARY)

    container_top = OUTER_MARGIN + genre_height + 32
    container_rect = (
        OUTER_MARGIN,
        container_top,
        CANVAS_WIDTH - OUTER_MARGIN,
        CANVAS_HEIGHT - OUTER_MARGIN,
    )
    _draw_rounded_rect(base, container_rect, RADIUS, fill=CONTAINER_COLOR)

    info_x = container_rect[0] + INNER_MARGIN
    info_y = container_rect[1] + INNER_MARGIN
    info_right = container_rect[2] - INNER_MARGIN

    location_parts: list[str] = []
    venue = getattr(ev, "venue_address", None) or getattr(ev, "venue", None)
    city = getattr(ev, "city", None)
    if venue:
        location_parts.append(venue)
        if city:
            location_parts.append(city)
    location_line = ", ".join(location_parts)

    date_line = ""
    date = getattr(ev, "date", None)
    time_obj = getattr(ev, "time", None)
    if date:
        date_line = f"{date.day}.{date.month}.{date.year}"
    time_line = ""
    if time_obj and not (time_obj.hour == 0 and time_obj.minute == 0):
        time_line = time_obj.strftime("%H:%M")

    row_height = 0
    if location_line or date_line or time_line:
        if location_line:
            draw.text((info_x, info_y), location_line, font=body_font, fill=TEXT_SECONDARY)
            row_height = max(row_height, body_font.getbbox(location_line)[3])
        else:
            row_height = max(row_height, body_font.getbbox("Ag")[3])

        right_lines = [line for line in (date_line, time_line) if line]
        if right_lines:
            line_height = body_font.getbbox("Ag")[3]
            for idx, line in enumerate(right_lines):
                line_width = body_font.getbbox(line)[2]
                draw.text(
                    (info_right - line_width, info_y + idx * (line_height + 6)),
                    line,
                    font=body_font,
                    fill=TEXT_SECONDARY,
                )
            row_height = max(row_height, len(right_lines) * (line_height + 6) - 6)

        info_y += row_height + 24
        _draw_dashed_line(
            base,
            container_rect[0] + INNER_MARGIN,
            info_y,
            container_rect[2] - INNER_MARGIN,
            color=BORDER_COLOR,
            dash=16,
            gap=12,
            width=2,
        )
        info_y += 32

    portrait_top = info_y
    available_height = container_rect[3] - INNER_MARGIN - portrait_top
    portrait_height = max(280, int(available_height * 0.6))

    outer_frame = (
        container_rect[0] + INNER_MARGIN,
        portrait_top,
        container_rect[2] - INNER_MARGIN,
        portrait_top + portrait_height,
    )

    _apply_shadow(base, outer_frame, RADIUS, blur=10, spread=12, color="#000000", opacity=0.35)
    _apply_shadow(base, outer_frame, RADIUS, blur=4, spread=0, color="#000000", opacity=0.25)
    _apply_shadow(base, outer_frame, RADIUS, blur=10, spread=8, color="#000000", opacity=0.18)

    _draw_rounded_rect(base, outer_frame, RADIUS, fill=CONTAINER_COLOR)
    mid_frame = _inset(outer_frame, 18)
    _draw_rounded_rect(base, mid_frame, RADIUS, fill=FRAME_DARK, outline=BORDER_COLOR, width=1)
    inner_frame = _inset(mid_frame, 24)
    _draw_rounded_rect(base, inner_frame, RADIUS, fill=FRAME_LIGHT)

    if portrait_png:
        try:
            portrait = Image.open(BytesIO(portrait_png)).convert("RGBA")
            fitted = _fit_cover(
                portrait,
                inner_frame[2] - inner_frame[0] - 32,
                inner_frame[3] - inner_frame[1] - 32,
            )
            px = inner_frame[0] + (inner_frame[2] - inner_frame[0] - fitted.width) // 2
            py = inner_frame[1] + (inner_frame[3] - inner_frame[1] - fitted.height) // 2
            base.alpha_composite(fitted, (px, py))
        except Exception:
            pass

    buffer = BytesIO()
    base.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def _draw_dashed_line(
    image: Image.Image,
    x0: int,
    y: int,
    x1: int,
    *,
    color: str,
    dash: int,
    gap: int,
    width: int,
) -> None:
    draw = ImageDraw.Draw(image)
    current = x0
    while current < x1:
        end = min(current + dash, x1)
        draw.line((current, y, end, y), fill=color, width=width)
        current = end + gap


def _fit_cover(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    if target_w <= 0 or target_h <= 0:
        return image
    w, h = image.size
    if w == 0 or h == 0:
        return image
    scale = max(target_w / w, target_h / h)
    new_size = (int(w * scale), int(h * scale))
    resized = image.resize(new_size, Image.LANCZOS)
    x = (new_size[0] - target_w) // 2
    y = (new_size[1] - target_h) // 2
    cropped = resized.crop((x, y, x + target_w, y + target_h))
    return cropped
