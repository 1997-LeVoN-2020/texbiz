"""
Механическая проверка сайта: коды ответов, внутренние ссылки, статика,
метатеги, JSON-LD, sitemap и robots.

Запуск из корня проекта:

    .venv/Scripts/python scripts/check_site.py

Ничего не запускает по сети и не поднимает сервер: работает через тестовый
клиент Django. Код возврата 1, если есть ошибки; предупреждения на код
возврата не влияют.
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402

from blog.models import Article  # noqa: E402
from web.models import Service  # noqa: E402

# Тестовый клиент не принимает хост testserver: он не в ALLOWED_HOSTS.
client = Client(HTTP_HOST="127.0.0.1")

errors = []
warnings = []

TITLE_MAX = 70  # длиннее обрезается в выдаче
DESC_MIN, DESC_MAX = 70, 180

STATIC_DIRS = [Path(p) for p in settings.STATICFILES_DIRS]


def err(page, text):
    errors.append(f"{page}: {text}")


def warn(page, text):
    warnings.append(f"{page}: {text}")


def pages():
    urls = [
        "/",
        "/uslugi/",
        "/resheniya/",
        "/booking/",
        "/kontakty/",
        "/privacy/",
        "/spasibo/",
        "/blog/",
    ]
    urls += [s.get_absolute_url() for s in Service.objects.published().exclude(body="")]
    urls += [a.get_absolute_url() for a in Article.objects.published()]
    return urls


def static_path(url):
    """/static/css/main.css -> путь на диске, если такой файл есть."""
    rel = url[len(settings.STATIC_URL):]
    for base in STATIC_DIRS:
        candidate = base / rel
        if candidate.exists():
            return candidate
    return None


def main():
    urls = pages()
    titles = Counter()
    descriptions = Counter()
    internal = set()
    statics = set()

    print(f"Проверяю {len(urls)} страниц\n")

    for url in urls:
        response = client.get(url)
        if response.status_code != 200:
            err(url, f"код ответа {response.status_code}")
            continue
        html = response.content.decode("utf-8")

        # Остатки шаблонного синтаксиса в готовой странице. Ловит и попавший
        # в фикстуру шаблонный код, и многострочный комментарий вида {# #},
        # который Django не считает комментарием и выводит как текст, — так
        # мои заметки попали на боевой сайт и висели поверх шапки.
        for marker in ("{{", "{%", "{#"):
            if marker in html:
                where = html.index(marker)
                err(url, f"в выводе остался шаблонный синтаксис {marker}: …{html[where:where + 60]}…")

        # Служебные страницы закрыты от индексации: длина метатегов для них не важна.
        indexed = 'name="robots" content="noindex' not in html

        title_match = re.search(r"<title>(.*?)</title>", html, re.S)
        if not title_match:
            err(url, "нет <title>")
        else:
            title = title_match.group(1).strip()
            titles[title] += 1
            if indexed and len(title) > TITLE_MAX:
                warn(url, f"title длиной {len(title)} знаков, обрежется в выдаче")

        desc_match = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
        if not desc_match:
            err(url, "нет meta description")
        else:
            description = desc_match.group(1).strip()
            descriptions[description] += 1
            if indexed and not DESC_MIN <= len(description) <= DESC_MAX:
                warn(url, f"description длиной {len(description)} знаков, норма {DESC_MIN}–{DESC_MAX}")

        canonical = re.search(r'<link rel="canonical" href="(.*?)"', html)
        expected = settings.SITE_URL + url
        if not canonical:
            err(url, "нет canonical")
        elif canonical.group(1) != expected:
            err(url, f"canonical {canonical.group(1)}, ожидался {expected}")

        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                err(url, f"JSON-LD не разбирается: {exc}")

        for href in re.findall(r'href="(/[^"#]*)"', html):
            internal.add(href)
        for ref in re.findall(r'(?:src|href)="(/static/[^"]+)"', html):
            statics.add(ref)

    # --- Внутренние ссылки ---------------------------------------------------

    checked = 0
    for href in sorted(internal):
        if href.startswith(settings.STATIC_URL):
            statics.add(href)
            continue
        checked += 1
        code = client.get(href).status_code
        if code != 200:
            err(href, f"внутренняя ссылка отдаёт {code}")

    # --- Статика (тестовый клиент её не отдаёт, проверяем на диске) ----------

    for ref in sorted(statics):
        if static_path(ref) is None:
            err(ref, "файл статики не найден на диске")

    # --- Уникальность метатегов ---------------------------------------------

    for title, count in titles.items():
        if count > 1:
            err("метатеги", f"title повторяется {count} раза: {title[:60]}")
    for description, count in descriptions.items():
        if count > 1:
            err("метатеги", f"description повторяется {count} раза: {description[:60]}")

    # --- Служебные адреса ----------------------------------------------------

    sitemap = client.get("/sitemap.xml")
    if sitemap.status_code != 200:
        err("/sitemap.xml", f"код ответа {sitemap.status_code}")
    else:
        # Django строит <loc> из хоста запроса, а не из SITE_URL: сравниваем по пути.
        locs = re.findall(r"<loc>(.*?)</loc>", sitemap.content.decode())
        listed = {urlparse(loc).path for loc in locs}
        missing = [u for u in urls if u not in listed and u not in ("/spasibo/", "/privacy/", "/kontakty/")]
        if missing:
            err("/sitemap.xml", f"страниц нет в карте сайта: {missing}")
        if "/privacy/" in listed or "/spasibo/" in listed:
            err("/sitemap.xml", "служебные страницы не должны быть в карте сайта")
        print(f"sitemap.xml: {len(locs)} адресов")

    robots = client.get("/robots.txt")
    if robots.status_code != 200:
        err("/robots.txt", f"код ответа {robots.status_code}")
    elif "Sitemap:" not in robots.content.decode():
        err("/robots.txt", "нет ссылки на sitemap")

    if client.get("/takoy-stranicy-net/").status_code != 404:
        err("404", "несуществующий адрес не отдаёт 404")

    # --- Итог ----------------------------------------------------------------

    print(f"внутренних ссылок проверено: {checked}")
    print(f"файлов статики проверено: {len(statics)}")

    if warnings:
        print(f"\nПредупреждения ({len(warnings)}):")
        for line in warnings:
            print("  ~", line)

    if errors:
        print(f"\nОшибки ({len(errors)}):")
        for line in errors:
            print("  !", line)
        return 1

    print("\nОшибок нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
