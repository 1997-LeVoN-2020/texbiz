"""
Растровые иконки и OG-картинка по брендбуку (лист «Знак», версия «иконка»).

Запуск из корня проекта:  python scripts/make_assets.py
Результат в static/img/: favicon-32.png, favicon-16.png, apple-touch-icon.png,
icon-192.png, icon-512.png, og-cover.png.

Шрифты для OG-картинки скачиваются с github.com/google/fonts во временную
папку; если сети нет, берутся системные Segoe UI и Consolas.
"""
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "img"

INK = "#15201B"
GROUND = "#ECF0ED"
ACCENT = "#14503A"
INK_2 = "#4A5B52"
PAPER = "#FFFFFF"

FONTS = {
    "onest": "https://github.com/google/fonts/raw/main/ofl/onest/Onest%5Bwght%5D.ttf",
    "mono": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}
FALLBACK = {
    "onest": "C:/Windows/Fonts/segoeuib.ttf",
    "mono": "C:/Windows/Fonts/consola.ttf",
}


def icon(size, supersample=4):
    """Иконка 48×48 из брендбука, отрисованная с запасом и уменьшенная."""
    s = size * supersample / 48
    img = Image.new("RGBA", (size * supersample, size * supersample), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def rect(x, y, w, h, r, fill):
        d.rounded_rectangle([x * s, y * s, (x + w) * s, (y + h) * s], radius=r * s, fill=fill)

    rect(0, 0, 48, 48, 8, INK)
    rect(12, 19, 6, 18, 1.5, GROUND)
    rect(21, 19, 6, 18, 1.5, GROUND)
    rect(30, 10, 6, 27, 1.5, GROUND)
    rect(21, 19, 6, 6, 1.5, ACCENT)
    rect(30, 10, 6, 9, 1.5, ACCENT)
    return img.resize((size, size), Image.LANCZOS)


def mark(draw, x, y, unit, ink=INK, accent=ACCENT):
    """Основной знак (без подложки) с масштабом unit = размер одной единицы сетки 48."""

    def rect(px, py, w, h, r, fill):
        draw.rounded_rectangle([x + px * unit, y + py * unit, x + (px + w) * unit, y + (py + h) * unit], radius=r * unit, fill=fill)

    rect(8, 18, 8, 24, 2, ink)
    rect(20, 18, 8, 24, 2, ink)
    rect(32, 6, 8, 36, 2, ink)
    rect(20, 18, 8, 8, 2, accent)
    rect(32, 6, 8, 12, 2, accent)


def load_font(key, size, weight=None):
    tmp = Path(tempfile.gettempdir()) / f"texbiz-{key}.ttf"
    if not tmp.exists():
        try:
            urllib.request.urlretrieve(FONTS[key], tmp)
        except Exception as exc:  # noqa: BLE001
            print(f"шрифт {key}: сеть недоступна ({exc}), беру системный")
    path = tmp if tmp.exists() else Path(FALLBACK[key])
    font = ImageFont.truetype(str(path), size)
    if weight is not None:
        try:
            font.set_variation_by_axes([weight])
        except Exception:  # noqa: BLE001
            pass
    return font


def og_cover():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), GROUND)
    d = ImageDraw.Draw(img)

    # Знак слева, крупно
    mark(d, 96, 150, 6.5)

    title = load_font("onest", 64, 700)
    word = load_font("onest", 30, 700)
    mono = load_font("mono", 22, 500)
    sub = load_font("onest", 28, 500)

    x = 460
    d.text((x, 150), "ТЕХ", font=word, fill=INK)
    w = d.textlength("ТЕХ", font=word)
    d.text((x + w + 2, 150), "БИЗ", font=word, fill=ACCENT)

    d.text((x, 215), "Автоматизация", font=title, fill=INK)
    d.text((x, 290), "отелей под ключ", font=title, fill=INK)
    d.text((x, 395), "1С · кассы · серверы · замковые системы", font=sub, fill=INK_2)
    d.text((x, 470), "TEX-BIZ.RU  ·  +7 938 511-13-31", font=mono, fill=ACCENT)

    d.rectangle([0, H - 8, W, H], fill=INK)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icon(32).save(OUT / "favicon-32.png")
    icon(16).save(OUT / "favicon-16.png")
    icon(180).save(OUT / "apple-touch-icon.png")
    icon(192).save(OUT / "icon-192.png")
    icon(512).save(OUT / "icon-512.png")
    og_cover().save(OUT / "og-cover.png", optimize=True)
    for p in sorted(OUT.glob("*.png")):
        print(p.name, p.stat().st_size, "байт")


if __name__ == "__main__":
    sys.exit(main())
