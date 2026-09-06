"""
Забирает шрифты Onest, PT Serif и JetBrains Mono к себе, чтобы сайт не зависел
от серверов Google.

Запуск из корня проекта:

    python scripts/fetch_fonts.py

Кладёт файлы .woff2 в static/fonts/ и собирает static/css/fonts.css с
правилами @font-face. Скрипт разовый и повторяемый: пересоберёт всё заново.

Зачем: обращение к fonts.googleapis.com и fonts.gstatic.com — это два лишних
соединения к чужим серверам до первой отрисовки текста. В России они бывают
медленными или недоступными, и тогда страница показывается запасным шрифтом
или не показывается вовсе. Свои файлы отдаются с того же домена и кэшируются
на год.

Лицензии позволяют: Onest и PT Serif — SIL Open Font License, JetBrains Mono —
Apache 2.0. Все три разрешают размещать файлы у себя.
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "static" / "fonts"
CSS_OUT = ROOT / "static" / "css" / "fonts.css"

# Современный User-Agent обязателен: без него Google отдаёт устаревший формат
# вместо woff2, который весит примерно вдвое меньше.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# Начертания ровно те, что использует main.css. Лишние не берём: каждое — файл.
FAMILIES = [
    ("Onest", "wght@400;500;600;700"),
    ("PT+Serif", "ital,wght@0,400;0,700;1,400"),
    ("JetBrains+Mono", "wght@400;500"),
]

# Кириллица нужна для текста, латиница для терминов вроде Wi-Fi и 1С-Отель.
KEEP_SUBSETS = {"cyrillic", "cyrillic-ext", "latin", "latin-ext"}


def get(url, binary=False):
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    return data if binary else data.decode("utf-8")


def parse_faces(css):
    """Разбирает ответ Google на отдельные @font-face со всеми полями."""
    faces = []
    for block in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S):
        subset, body = block

        def field(name):
            match = re.search(rf"{name}:\s*([^;]+);", body)
            return match.group(1).strip() if match else None

        url_match = re.search(r"url\((https://[^)]+\.woff2)\)", body)
        if not url_match:
            continue
        faces.append(
            {
                "subset": subset,
                "family": field("font-family").strip("'\""),
                "style": field("font-style") or "normal",
                "weight": field("font-weight") or "400",
                "range": field("unicode-range"),
                "url": url_match.group(1),
            }
        )
    return faces


def main():
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for old in FONT_DIR.glob("*.woff2"):
        old.unlink()

    rules = [
        "/* Шрифты, размещённые у себя. Собрано scripts/fetch_fonts.py — правки",
        "   вносить туда, этот файл перезаписывается целиком.",
        "",
        "   Onest и PT Serif — SIL Open Font License, JetBrains Mono — Apache 2.0.",
        "   Все три лицензии разрешают размещение у себя. */",
        "",
    ]
    total = 0

    for family, axis in FAMILIES:
        url = f"https://fonts.googleapis.com/css2?family={family}:{axis}&display=swap"
        print(f"{family.replace('+', ' ')}")
        faces = [f for f in parse_faces(get(url)) if f["subset"] in KEEP_SUBSETS]
        if not faces:
            print("  ОШИБКА: ни одного подходящего набора символов")
            return 1

        for face in faces:
            slug = face["family"].lower().replace(" ", "-")
            italic = "-italic" if face["style"] == "italic" else ""
            name = f"{slug}-{face['weight']}{italic}-{face['subset']}.woff2"
            data = get(face["url"], binary=True)
            (FONT_DIR / name).write_bytes(data)
            total += len(data)
            print(f"  {name}  {len(data) // 1024} КБ")

            rules += [
                "@font-face {",
                f"  font-family: '{face['family']}';",
                f"  font-style: {face['style']};",
                f"  font-weight: {face['weight']};",
                "  font-display: swap;",
                f"  src: url('../fonts/{name}') format('woff2');",
                f"  unicode-range: {face['range']};" if face["range"] else "",
                "}",
                "",
            ]

    CSS_OUT.write_text("\n".join(line for line in rules if line != "" or True), encoding="utf-8")
    print(f"\nfonts.css собран, файлов {len(list(FONT_DIR.glob('*.woff2')))}, всего {total // 1024} КБ")
    print("Браузер скачивает только нужные наборы символов, а не всё сразу.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
