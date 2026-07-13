"""ТЕХБИЗ — сайт как одно Flask-приложение: рендерит страницы по запросу
и обрабатывает форму заявки (POST /send).

Usage: python app.py
"""
import hashlib
import os
import smtplib
import time
from collections import defaultdict
from datetime import date
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "src" / "static"

SITE_URL = "https://tex-biz.ru"

ROBOTS_DEFAULT = "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"

# Single source of truth for every page: routing, SEO metadata, sitemap entry.
PAGES = [
    {
        "id": "home", "url_path": "", "template": "pages/index.html",
        "title": "Автоматизация отелей под ключ в 1С | Кассы, серверы, замки | ТЕХБИЗ",
        "description": "ТЕХБИЗ внедряет 1С для отелей, настраивает онлайн-кассы, серверы и замковые системы. Комплексная автоматизация гостиниц под ключ с поддержкой 24/7.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Автоматизация отелей под ключ в 1С | ТЕХБИЗ",
        "og_description": "Внедрение 1С для отелей, онлайн-кассы, серверная инфраструктура и замковые системы. Пусконаладка и сопровождение.",
        "priority": "1.0", "changefreq": "weekly",
    },
    {
        "id": "booking", "url_path": "booking/", "template": "pages/booking.html",
        "title": "Модуль онлайн-бронирования для сайта отеля | ТЕХБИЗ",
        "description": "Онлайн-бронирование и оплата номеров прямо на сайте отеля, с интеграцией в 1С-Отель. ЮKassa, Сбербанк Эквайринг, PayKeeper — без комиссии агрегаторов.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Модуль онлайн-бронирования для сайта отеля | ТЕХБИЗ",
        "og_description": "Прямые брони и оплата на сайте отеля с интеграцией в 1С-Отель — без комиссии агрегаторов.",
        "priority": "0.9", "changefreq": "weekly",
    },
    {
        "id": "svc_1c", "url_path": "1c-avtomatizaciya-otelya/", "template": "pages/1c-avtomatizaciya-otelya.html",
        "title": "Автоматизация 1С для отеля: внедрение и настройка | ТЕХБИЗ",
        "description": "Внедрение и настройка 1С для отеля: учёт, заселение, отчётность, интеграция с кассами и PMS. Запуск от 5 дней, поддержка 24/7.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Автоматизация 1С для отеля | ТЕХБИЗ",
        "og_description": "Внедрение и настройка 1С для отеля: учёт, заселение, отчётность, интеграция с кассами и PMS.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "svc_kassy", "url_path": "onlain-kassy-dlya-gostinicy/", "template": "pages/onlain-kassy-dlya-gostinicy.html",
        "title": "Настройка онлайн-касс для гостиницы (54-ФЗ, ОФД) | ТЕХБИЗ",
        "description": "Подключение и настройка онлайн-касс для отеля: 54-ФЗ, ОФД, эквайринг, интеграция с 1С. Кассы работают без сбоев даже в высокий сезон.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Настройка онлайн-касс для гостиницы | ТЕХБИЗ",
        "og_description": "Подключение и настройка онлайн-касс для отеля: 54-ФЗ, ОФД, эквайринг, интеграция с 1С.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "svc_servers", "url_path": "nastroika-serverov-otelya/", "template": "pages/nastroika-serverov-otelya.html",
        "title": "Настройка серверов и сети для отеля | ТЕХБИЗ",
        "description": "Проектирование и настройка серверной инфраструктуры и сети отеля: резервирование, Wi-Fi, отказоустойчивость. Меньше простоев в высокий сезон.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Настройка серверов и сети для отеля | ТЕХБИЗ",
        "og_description": "Проектирование и настройка серверной инфраструктуры и сети отеля: резервирование, Wi-Fi, отказоустойчивость.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "svc_locks", "url_path": "integraciya-zamkovyh-sistem/", "template": "pages/integraciya-zamkovyh-sistem.html",
        "title": "Интеграция замковых систем для отеля | ТЕХБИЗ",
        "description": "Интеграция электронных замков и карт доступа с 1С-Отель: автоматическая выдача ключей, контроль доступа гостей и персонала.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Интеграция замковых систем для отеля | ТЕХБИЗ",
        "og_description": "Интеграция электронных замков и карт доступа с 1С-Отель: автоматическая выдача ключей, контроль доступа.",
        "priority": "0.8", "changefreq": "monthly",
    },
    {
        "id": "privacy", "url_path": "privacy/", "template": "pages/privacy.html",
        "title": "Политика обработки персональных данных | ТЕХБИЗ",
        "description": "Политика обработки персональных данных компании ТЕХБИЗ: какие данные собираются через форму заявки, цели и сроки обработки, права субъекта данных.",
        "robots": "noindex, follow",
        "og": False, "icon192": False,
        "in_sitemap": False,
    },
    {
        "id": "blog_index", "url_path": "blog/", "template": "pages/blog/index.html",
        "title": "Блог об автоматизации отелей | ТЕХБИЗ",
        "description": "Статьи об автоматизации гостиничного бизнеса: внедрение 1С, выбор онлайн-касс, серверная инфраструктура и замковые системы для отелей.",
        "og": True, "og_type": "website", "icon192": True,
        "og_title": "Блог об автоматизации отелей | ТЕХБИЗ",
        "og_description": "Статьи об автоматизации гостиничного бизнеса: 1С, онлайн-кассы, серверы, замковые системы.",
        "priority": "0.7", "changefreq": "weekly",
    },
    {
        "id": "blog_1c", "url_path": "blog/1c-avtomatizaciya-otelya-s-chego-nachat/", "template": "pages/blog/1c-avtomatizaciya-otelya-s-chego-nachat.html",
        "title": "Автоматизация 1С для отеля: с чего начать | Блог ТЕХБИЗ",
        "description": "Пошаговый план внедрения 1С для отеля: аудит текущих процессов, приоритетные модули, типичные ошибки и реальные сроки запуска.",
        "og": True, "og_type": "article", "icon192": False,
        "og_title": "Автоматизация 1С для отеля: с чего начать",
        "og_description": "Пошаговый план внедрения 1С для отеля: аудит, приоритетные модули, типичные ошибки и реальные сроки.",
        "priority": "0.6", "changefreq": "yearly",
    },
    {
        "id": "blog_kassy", "url_path": "blog/kak-vybrat-onlayn-kassu-dlya-gostinicy/", "template": "pages/blog/kak-vybrat-onlayn-kassu-dlya-gostinicy.html",
        "title": "Как выбрать онлайн-кассу для гостиницы | Блог ТЕХБИЗ",
        "description": "Требования 54-ФЗ, на что смотреть при выборе онлайн-кассы для отеля и как не остаться без работающей кассы в высокий сезон.",
        "og": True, "og_type": "article", "icon192": False,
        "og_title": "Как выбрать онлайн-кассу для гостиницы",
        "og_description": "Требования 54-ФЗ и на что смотреть при выборе ККТ для отеля.",
        "priority": "0.6", "changefreq": "yearly",
    },
]

PAGES_BY_ID = {p["id"]: p for p in PAGES}

app = Flask(
    __name__,
    template_folder=str(ROOT / "src" / "templates"),
    static_folder=str(STATIC_DIR),
    static_url_path="",
)


def _asset_version():
    # Cache-busting query string for styles.css/script.js, computed once at
    # process start (a fresh value appears on the next deploy/restart).
    h = hashlib.sha256()
    for name in ("styles.css", "script.js"):
        h.update((STATIC_DIR / name).read_bytes())
    return h.hexdigest()[:10]


ASSET_VERSION = _asset_version()

# Sitemap <lastmod> equivalent to the old "build date" -- now there's no
# build step, so this is the date the app process last started (deploy/
# restart), computed once rather than on every request.
DEPLOY_DATE = date.today().isoformat()


def url_for_page(page_id, anchor=None):
    target = PAGES_BY_ID[page_id]
    href = "/" + target["url_path"]
    if anchor:
        href += f"#{anchor}"
    return href


def asset(rel_path):
    return "/" + rel_path


@app.context_processor
def inject_globals():
    # Intentionally shadows Flask's own url_for inside Jinja rendering --
    # templates never call the real flask.url_for, only this simpler one
    # keyed by PAGES id. Python code can still use flask.url_for normally.
    return {"url_for": url_for_page, "asset": asset, "SITE_URL": SITE_URL, "ASSET_VERSION": ASSET_VERSION}


def make_page_view(page):
    # Factory, not a closure over the loop variable directly -- otherwise
    # every route would render whichever page the loop last held.
    def view():
        ctx_page = {**page}
        ctx_page.setdefault("robots", ROBOTS_DEFAULT)
        ctx_page.setdefault("og_type", "website")
        canonical_url = f"{SITE_URL}/{page['url_path']}"
        return render_template(page["template"], page=ctx_page, canonical_url=canonical_url)
    view.__name__ = f"page_{page['id']}"
    return view


for _page in PAGES:
    app.add_url_rule(f"/{_page['url_path']}", endpoint=_page["id"], view_func=make_page_view(_page))


@app.errorhandler(404)
def not_found(_e):
    page = {
        "title": "Страница не найдена | ТЕХБИЗ",
        "description": "Запрошенная страница не найдена.",
        "robots": "noindex, follow",
        "og": False,
        "og_type": "website",
        "icon192": True,
    }
    html = render_template("pages/404.html", page=page, canonical_url=f"{SITE_URL}/404.html")
    return html, 404


@app.route("/sitemap.xml")
def sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in PAGES:
        if page.get("in_sitemap") is False:
            continue
        loc = f"{SITE_URL}/{page['url_path']}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{DEPLOY_DATE}</lastmod>")
        lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        lines.append(f"    <priority>{page['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return Response("\n".join(lines) + "\n", mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return Response(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", mimetype="text/plain"
    )


# --- Lead-generation form (merged from the previous separate pyapp) ---

TO_ADDR = "info@tex-biz.ru"
FROM_ADDR = os.environ.get("MAIL_FROM", "noreply@tex-biz.ru")
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

RATE_LIMIT_WINDOW = 600  # seconds
RATE_LIMIT_MAX = 5  # requests per IP per window

# In-memory only — resets per worker process on restart, and isn't shared
# across multiple Passenger worker processes. Good enough to blunt naive
# spam/flooding on this low-traffic lead form without adding a dependency.
_rate_limit_hits = defaultdict(list)


def clean(value):
    return (value or "").replace("\r", " ").replace("\n", " ").strip()


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(ip):
    now = time.time()
    hits = _rate_limit_hits[ip]
    hits[:] = [t for t in hits if now - t < RATE_LIMIT_WINDOW]
    if len(hits) >= RATE_LIMIT_MAX:
        return True
    hits.append(now)
    return False


@app.route("/send", methods=["POST"])
def send():
    if rate_limited(client_ip()):
        return jsonify(ok=False, error="rate_limited"), 429

    name = clean(request.form.get("name"))
    phone = clean(request.form.get("phone"))
    object_type = clean(request.form.get("object"))
    message = clean(request.form.get("message"))
    honeypot = clean(request.form.get("website"))
    agree = request.form.get("agree")

    # Honeypot: bots fill hidden fields, humans don't. Pretend success without sending.
    if honeypot:
        return jsonify(ok=True)

    if not name or not phone or not object_type or not agree:
        return jsonify(ok=False, error="missing_fields"), 422

    body = (
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Тип объекта: {object_type}\n"
        f"Задача: {message or '-'}\n"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header("Новая заявка с сайта ТЕХБИЗ", "utf-8")
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = FROM_ADDR

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USER and SMTP_PASSWORD:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
    except Exception:
        return jsonify(ok=False, error="send_failed"), 500

    return jsonify(ok=True)


# Passenger (ISPmanager) imports this exact name as the WSGI entry point.
application = app

if __name__ == "__main__":
    app.run(debug=True)
