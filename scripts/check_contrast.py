"""
Проверка контраста по WCAG для пар цветов, которые реально встречаются на сайте.

Запуск из корня проекта:

    python scripts/check_contrast.py

Цвета берутся из блока :root в static/css/main.css, пары перечислены ниже
вручную: автоматически определить, что на чём лежит, нельзя.

Пороги: 4.5 для обычного текста, 3.0 для крупного текста (от 24 px или
от 19 px жирного) и для границ и значков, несущих смысл.

Граница элемента управления (кнопки, поля ввода) обязана давать 3.0: по ней
человек и понимает, что перед ним элемент управления. Граница оформления
(рамка карточки, разделитель, чип-подпись) под это требование не подпадает —
такие пары печатаются для сведения и на код возврата не влияют.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "static" / "css" / "main.css"

TEXT = 4.5
LARGE = 3.0

INFO = None  # для сведения: на код возврата не влияет

# (токен переднего плана, токен фона, где встречается, порог)
PAIRS = [
    ("--ink", "--ground", "основной текст на фоне страницы", TEXT),
    ("--ink-2", "--ground", "вторичный текст на фоне страницы", TEXT),
    ("--ink-3", "--ground", "подписи на фоне страницы", TEXT),
    ("--accent", "--ground", "ссылка на фоне страницы", TEXT),
    ("--ink", "--paper", "текст в карточке", TEXT),
    ("--ink-2", "--paper", "текст карточки, описание услуги", TEXT),
    ("--ink-3", "--paper", "дата статьи, надписи в подвале", TEXT),
    ("--accent", "--paper", "ссылка в карточке, надзаголовок", TEXT),
    ("--ink", "--paper-2", "текст в поле ввода", TEXT),
    ("--ink-3", "--paper-2", "подсказка в поле ввода", TEXT),
    ("--on-accent", "--accent", "текст на кнопке", TEXT),
    ("--on-accent", "--accent-hover", "текст на кнопке при наведении", TEXT),
    ("--ink", "--accent-soft", "заголовок в блоке продукта", TEXT),
    ("--ink-2", "--accent-soft", "текст в блоке продукта", TEXT),
    ("--accent", "--accent-soft", "значок услуги, надзаголовок в блоке", LARGE),
    ("--error", "--paper", "ошибка под полем формы", TEXT),
    ("--error", "--ground", "ошибка на фоне страницы", TEXT),
    # Элементы управления: граница обязана читаться
    ("--ink-3", "--paper", "граница поля ввода и кнопки на карточке", LARGE),
    ("--ink-3", "--ground", "граница кнопки и якорной ссылки на фоне", LARGE),
    ("--ink-3", "--paper-2", "граница поля ввода на своей заливке", LARGE),
    ("--accent", "--paper-2", "флажок согласия", LARGE),
    # Оформление: требование 1.4.11 не распространяется
    ("--line", "--paper", "разделитель и рамка карточки", INFO),
    ("--line-2", "--ground", "рамка чипа-подписи", INFO),
]


def tokens():
    css = CSS.read_text(encoding="utf-8")
    root = re.search(r":root\s*\{(.*?)\}", css, re.S).group(1)
    found = dict(re.findall(r"(--[a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", root))
    return found


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))

    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = channel(r), channel(g), channel(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = luminance(fg), luminance(bg)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def main():
    colors = tokens()
    failures = 0

    print(f"{'пара':<52} {'значение':>9} {'порог':>6}  итог")
    print("-" * 82)

    checked = 0
    for fg, bg, where, threshold in PAIRS:
        if fg not in colors or bg not in colors:
            print(f"{where:<52} {'—':>9} {'—':>6}  токен не найден: {fg} или {bg}")
            failures += 1
            continue
        value = ratio(colors[fg], colors[bg])
        if threshold is INFO:
            print(f"{where:<52} {value:>9.2f} {'—':>6}  оформление")
            continue
        checked += 1
        ok = value >= threshold
        if not ok:
            failures += 1
        print(f"{where:<52} {value:>9.2f} {threshold:>6.1f}  {'ок' if ok else 'НЕ ПРОХОДИТ'}")

    print()
    if failures:
        print(f"Пар ниже нормы: {failures}")
        return 1
    print(f"Все {checked} пар с требованием проходят WCAG AA.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
