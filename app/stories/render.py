from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pathlib import Path

W, H = 1080, 1920
FONT_H1 = Path("assets/Inter-SemiBold.ttf")
FONT_H2 = Path("assets/Inter-Medium.ttf")

def _wrap(draw, text, font, width_px):
    words = (text or "").split()
    lines, line = [], []
    for w in words:
        test = " ".join(line + [w])
        if draw.textlength(test, font=font) <= width_px:
            line.append(w)
        else:
            lines.append(" ".join(line)); line=[w]
    if line: lines.append(" ".join(line))
    return lines

def render_story(events, title="Hoy en BA / Сегодня в BA"):
    img = Image.new("RGB", (W, H), (11,16,32))
    draw = ImageDraw.Draw(img)
    # простой вертикальный градиент
    for y in range(H):
        ratio = y / H
        r = int(10 + ratio * 120)
        g = int(10 + ratio * 240)
        b = int(40 + (1-ratio) * 200)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    draw = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(str(FONT_H1), 64) if FONT_H1.exists() else ImageFont.load_default()
    f2 = ImageFont.truetype(str(FONT_H2), 40) if FONT_H2.exists() else ImageFont.load_default()
    draw.text((60, 70), title, font=f1, fill=(220,245,255))
    y = 220
    card_h = 480
    pad = 36
    for ev in events[:3]:
        draw.rounded_rectangle([40, y, W-40, y+card_h], radius=28, fill=(18,24,46,255))
        poster_box = [60, y+40, 60+360, y+40+360]
        draw.rounded_rectangle(poster_box, radius=18, fill=(28,38,74,255))
        tx = 60+360+36; tw = W - tx - 60
        title_lines = _wrap(draw, ev.title, f1, tw)
        draw.text((tx, y+36), "\n".join(title_lines[:2]), font=f1, fill=(240,240,255))
        meta = f"🗓 {ev.date.isoformat()} {ev.time.strftime('%H:%M') if ev.time else ''}\n"                    f"📍 {ev.venue or '—'}\n"                    f"🎶 {', '.join(ev.genres or [])}"
        draw.text((tx, y+200), meta, font=f2, fill=(210,220,240))
        if getattr(ev, 'source_link', None):
            short = ev.source_link.replace("https://","").replace("http://","")
            draw.text((tx, y+320), f"🔗 {short}", font=f2, fill=(160,220,255))
        y += card_h + pad
    b = BytesIO(); img.save(b, format="PNG", optimize=True); b.seek(0)
    return b
