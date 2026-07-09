"""Builds the static site from src/templates into dist/.

Usage: python build.py
"""
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
SRC = ROOT / "src"
TEMPLATES_DIR = SRC / "templates"
STATIC_DIR = SRC / "static"
DIST = ROOT / "dist"

SITE_URL = "https://tex-biz.ru"

ROBOTS_DEFAULT = "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"

# Single source of truth for every page: routing, SEO metadata, sitemap entry.
PAGES = [
    {
        "id": "home", "url_path": "", "template": "pages/index.html",
        "title": "Автоматизация отелей под ключ в 1С | Кассы, серверы, замки | ТЕХБИЗ",
        "description": "ТЕХБИЗ внедряет 1С для отелей, настраивает онлайн-кассы, серверы и замковые системы. Комплексная автоматизация гостиниц под ключ с поддержкой 24/7.",
        "og": True, "og_type": "website", "hreflang": True, "icon192": True,
        "og_title": "Автоматизация отелей под ключ в 1С | ТЕХБИЗ",
        "og_description": "Внедрение 1С для отелей, онлайн-кассы, серверная инфраструктура и замковые системы. Пусконаладка и сопровождение.",
        "priority": "1.0", "changefreq": "weekly",
    },
    {
        "id": "booking", "url_path": "booking/", "template": "pages/booking.html",
        "title": "Модуль онлайн-бронирования для сайта отеля | ТЕХБИЗ",
        "description": "Онлайн-бронирование и оплата номеров прямо на сайте отеля, с интеграцией в 1С-Отель. ЮKassa и Сбербанк Эквайринг, без комиссии агрегаторов.",
        "og": True, "og_type": "website", "hreflang": False, "icon192": True,
        "og_title": "Модуль онлайн-бронирования для сайта отеля | ТЕХБИЗ",
        "og_description": "Прямые брони и оплата на сайте отеля с интеграцией в 1С-Отель — без комиссии агрегаторов.",
        "priority": "0.9", "changefreq": "weekly",
    },
    {
        "id": "svc_1c", "url_path": "1c-avtomatizaciya-otelya/", "template": "pages/1c-avtomatizaciya-otelya.html",
        "title": "Автоматизация 1С для отеля: внедрение и настройка | ТЕХБИЗ",
        "description": "Внедрение и настройка 1С для отеля: учёт, заселение, отчётность, интеграция с кассами и PMS. Запуск от 5 дней, поддержка 24/7.",
        "og": True, "og_type": "website", "hreflang": False, "icon192": True,
        "og_title": "Автоматизация 1С для отеля | ТЕХБИЗ",
        "og_description": "Внедрение и настройка 1С для отеля: учёт, заселение, отчётность, интеграция с кассами и PMS.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "svc_kassy", "url_path": "onlain-kassy-dlya-gostinicy/", "template": "pages/onlain-kassy-dlya-gostinicy.html",
        "title": "Настройка онлайн-касс для гостиницы (54-ФЗ, ОФД) | ТЕХБИЗ",
        "description": "Подключение и настройка онлайн-касс для отеля: 54-ФЗ, ОФД, эквайринг, интеграция с 1С. Кассы работают без сбоев даже в высокий сезон.",
        "og": True, "og_type": "website", "hreflang": False, "icon192": True,
        "og_title": "Настройка онлайн-касс для гостиницы | ТЕХБИЗ",
        "og_description": "Подключение и настройка онлайн-касс для отеля: 54-ФЗ, ОФД, эквайринг, интеграция с 1С.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "svc_servers", "url_path": "nastroika-serverov-otelya/", "template": "pages/nastroika-serverov-otelya.html",
        "title": "Настройка серверов и сети для отеля | ТЕХБИЗ",
        "description": "Проектирование и настройка серверной инфраструктуры и сети отеля: резервирование, Wi-Fi, отказоустойчивость. Меньше простоев в высокий сезон.",
        "og": True, "og_type": "website", "hreflang": False, "icon192": True,
        "og_title": "Настройка серверов и сети для отеля | ТЕХБИЗ",
        "og_description": "Проектирование и настройка серверной инфраструктуры и сети отеля: резервирование, Wi-Fi, отказоустойчивость.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "svc_locks", "url_path": "integraciya-zamkovyh-sistem/", "template": "pages/integraciya-zamkovyh-sistem.html",
        "title": "Интеграция замковых систем для отеля | ТЕХБИЗ",
        "description": "Интеграция электронных замков и карт доступа с 1С-Отель: автоматическая выдача ключей, контроль доступа гостей и персонала.",
        "og": True, "og_type": "website", "hreflang": False, "icon192": True,
        "og_title": "Интеграция замковых систем для отеля | ТЕХБИЗ",
        "og_description": "Интеграция электронных замков и карт доступа с 1С-Отель: автоматическая выдача ключей, контроль доступа.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "privacy", "url_path": "privacy/", "template": "pages/privacy.html",
        "title": "Политика обработки персональных данных | ТЕХБИЗ",
        "description": "Политика обработки персональных данных компании ТЕХБИЗ: какие данные собираются через форму заявки, цели и сроки обработки, права субъекта данных.",
        "robots": "noindex, follow",
        "og": False, "hreflang": False, "icon192": False,
        "in_sitemap": False,
    },
    {
        "id": "blog_index", "url_path": "blog/", "template": "pages/blog/index.html",
        "title": "Блог об автоматизации отелей | ТЕХБИЗ",
        "description": "Статьи об автоматизации гостиничного бизнеса: внедрение 1С, выбор онлайн-касс, серверная инфраструктура и замковые системы для отелей.",
        "og": True, "og_type": "website", "hreflang": False, "icon192": True,
        "og_title": "Блог об автоматизации отелей | ТЕХБИЗ",
        "og_description": "Статьи об автоматизации гостиничного бизнеса: 1С, онлайн-кассы, серверы, замковые системы.",
        "priority": "0.7", "changefreq": "weekly",
    },
    {
        "id": "blog_1c", "url_path": "blog/1c-avtomatizaciya-otelya-s-chego-nachat/", "template": "pages/blog/1c-avtomatizaciya-otelya-s-chego-nachat.html",
        "title": "Автоматизация 1С для отеля: с чего начать | Блог ТЕХБИЗ",
        "description": "Пошаговый план внедрения 1С для отеля: аудит текущих процессов, приоритетные модули, типичные ошибки и реальные сроки запуска.",
        "og": True, "og_type": "article", "hreflang": False, "icon192": False,
        "og_title": "Автоматизация 1С для отеля: с чего начать",
        "og_description": "Пошаговый план внедрения 1С для отеля: аудит, приоритетные модули, типичные ошибки и реальные сроки.",
        "priority": "0.6", "changefreq": "yearly",
    },
    {
        "id": "blog_kassy", "url_path": "blog/kak-vybrat-onlayn-kassu-dlya-gostinicy/", "template": "pages/blog/kak-vybrat-onlayn-kassu-dlya-gostinicy.html",
        "title": "Как выбрать онлайн-кассу для гостиницы | Блог ТЕХБИЗ",
        "description": "Требования 54-ФЗ, на что смотреть при выборе онлайн-кассы для отеля и как не остаться без работающей кассы в высокий сезон.",
        "og": True, "og_type": "article", "hreflang": False, "icon192": False,
        "og_title": "Как выбрать онлайн-кассу для гостиницы",
        "og_description": "Требования 54-ФЗ и на что смотреть при выборе ККТ для отеля.",
        "priority": "0.6", "changefreq": "yearly",
    },
]

PAGES_BY_ID = {p["id"]: p for p in PAGES}


def _depth(url_path):
    return len([seg for seg in url_path.split("/") if seg])


def _root_prefix(url_path):
    d = _depth(url_path)
    return "../" * d


def make_url_for(current_url_path):
    def url_for(page_id, anchor=None):
        target = PAGES_BY_ID[page_id]
        target_path = target["url_path"]

        if target_path == current_url_path:
            return f"#{anchor}" if anchor else "./"

        href = _root_prefix(current_url_path) + target_path if target_path else (_root_prefix(current_url_path) or "./")
        if anchor:
            href += f"#{anchor}"
        return href
    return url_for


def make_asset(current_url_path):
    def asset(rel_path):
        return _root_prefix(current_url_path) + rel_path
    return asset


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # Static passthrough (styles.css, script.js, .htaccess, assets/).
    for item in STATIC_DIR.iterdir():
        target = DIST / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )

    for page in PAGES:
        page = {**page}
        page.setdefault("robots", ROBOTS_DEFAULT)
        page.setdefault("og_type", "website")

        canonical_url = f"{SITE_URL}/{page['url_path']}"
        context = {
            "page": page,
            "SITE_URL": SITE_URL,
            "canonical_url": canonical_url,
            "url_for": make_url_for(page["url_path"]),
            "asset": make_asset(page["url_path"]),
        }

        template = env.get_template(page["template"])
        html = template.render(**context)

        out_dir = DIST / page["url_path"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"built {page['id']:14s} -> dist/{page['url_path']}index.html")

    build_404(env)

    build_sitemap()
    print(f"\nDone. Output in {DIST}")


def build_404(env):
    # Not a normal routable page: lives at dist/404.html (root), excluded from
    # sitemap/url_for. .htaccess points ErrorDocument 404 here.
    page = {
        "title": "Страница не найдена | ТЕХБИЗ",
        "description": "Запрошенная страница не найдена.",
        "robots": "noindex, follow",
        "og": False,
        "og_type": "website",
        "hreflang": False,
        "icon192": True,
    }
    context = {
        "page": page,
        "SITE_URL": SITE_URL,
        "canonical_url": f"{SITE_URL}/404.html",
        "url_for": make_url_for(""),
        "asset": make_asset(""),
    }
    template = env.get_template("pages/404.html")
    html = template.render(**context)
    (DIST / "404.html").write_text(html, encoding="utf-8")
    print(f"built {'404':14s} -> dist/404.html")


def build_sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in PAGES:
        if page.get("in_sitemap") is False:
            continue
        loc = f"{SITE_URL}/{page['url_path']}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append("    <lastmod>2026-07-08</lastmod>")
        lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        lines.append(f"    <priority>{page['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
