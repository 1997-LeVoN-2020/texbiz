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
from markupsafe import Markup

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
    {
        "id": "blog_servers", "url_path": "blog/kak-vybrat-server-i-set-dlya-otelya/", "template": "pages/blog/kak-vybrat-server-i-set-dlya-otelya.html",
        "title": "Как выбрать сервер и сеть для отеля | Блог ТЕХБИЗ",
        "description": "Резервирование, разделение Wi-Fi для гостей и персонала, мониторинг 24/7 и защита данных — как спроектировать серверную инфраструктуру отеля без сбоев.",
        "og": True, "og_type": "article", "icon192": False,
        "og_title": "Как выбрать сервер и сеть для отеля",
        "og_description": "Резервирование, Wi-Fi для гостей и персонала и мониторинг 24/7 — как спроектировать серверную инфраструктуру отеля.",
        "priority": "0.6", "changefreq": "yearly",
    },
    {
        "id": "blog_locks", "url_path": "blog/kak-vybrat-zamkovuyu-sistemu-dlya-otelya/", "template": "pages/blog/kak-vybrat-zamkovuyu-sistemu-dlya-otelya.html",
        "title": "Как выбрать электронную замковую систему для отеля | Блог ТЕХБИЗ",
        "description": "На что обратить внимание при выборе и внедрении электронных замков для отеля: интеграция с 1С, уровни доступа, аварийный доступ, совместимость.",
        "og": True, "og_type": "article", "icon192": False,
        "og_title": "Как выбрать электронную замковую систему для отеля",
        "og_description": "Интеграция с 1С, уровни доступа, аварийный доступ и совместимость — на что смотреть при выборе замковой системы.",
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


# One glyph per distinct real-world concept -- OTA and PMS share SYNC because
# both mean "data stays live with the source system", not because we ran out
# of ideas. Replaces the old text-abbreviation badges (1C, KKT, RPT...).
_SERVICE_ICON_PATHS = {
    "1C": '<ellipse cx="12" cy="6" rx="7" ry="2.5"/><path d="M5 6v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6"/><path d="M5 12v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6"/>',
    "KKT": '<path d="M7 3h10v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5V3z"/><path d="M9 7h6M9 10h6M9 13h4"/>',
    "RPT": '<path d="M4 16l5-5 4 3 6-7"/><path d="M4 20h16"/>',
    "OTA": '<path d="M20 11A8 8 0 006.3 6.3M4 13a8 8 0 0013.7 4.7"/><path d="M4 4v5h5M20 20v-5h-5"/>',
    "PMS": '<path d="M20 11A8 8 0 006.3 6.3M4 13a8 8 0 0013.7 4.7"/><path d="M4 4v5h5M20 20v-5h-5"/>',
    "EDU": '<path d="M12 6c-2-1.5-5-2-8-1v13c3-1 6-.5 8 1 2-1.5 5-2 8-1V5c-3-1-6-.5-8 1z"/><path d="M12 6v13"/>',
    "OPS": '<path d="M4 13v-1a8 8 0 0116 0v1"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/><path d="M20 19v1a3 3 0 01-3 3h-3"/>',
    "BOOK": '<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/><path d="M9 15l2 2 4-4"/>',
    "PAY": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><path d="M7 14h4"/>',
    "15": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/>',
    "SRCH": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M20 20l-4.8-4.8"/>',
    "RUM": '<path d="M3 19v-7a3 3 0 013-3h12a3 3 0 013 3v7"/><path d="M3 15h18"/><path d="M7 12v-1a2 2 0 012-2h2a2 2 0 012 2v1"/>',
    "KID": '<circle cx="9" cy="7" r="3.2"/><path d="M3.5 20v-1.2A5.3 5.3 0 018.8 13.5h.4a5.3 5.3 0 015.3 5.3V20"/><circle cx="18" cy="10" r="2.2"/><path d="M14.8 20v-.9a3.7 3.7 0 013.7-3.7 3.7 3.7 0 013.7 3.7"/>',
    "CRT": '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/>',
    "ADM": '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.2M12 18.8V21M4.9 4.9l1.6 1.6M17.5 17.5l1.6 1.6M3 12h2.2M18.8 12H21M4.9 19.1l1.6-1.6M17.5 6.5l1.6-1.6"/>',
    "OFD": '<path d="M7 18a4.5 4.5 0 01-.7-8.9A5.5 5.5 0 0117 8.5 4 4 0 0117 17H7z"/><path d="M12 14V9M9.5 11.5L12 9l2.5 2.5"/>',
    "RES": '<rect x="4" y="7" width="12" height="12" rx="1.5"/><path d="M8 7V6a2 2 0 012-2h9a2 2 0 012 2v9a2 2 0 01-2 2h-1"/>',
    "SRV": '<rect x="4" y="4" width="16" height="6" rx="1.2"/><rect x="4" y="14" width="16" height="6" rx="1.2"/><path d="M7.5 7h.01M7.5 17h.01"/>',
    "WIFI": '<path d="M4 9a13 13 0 0116 0"/><path d="M7.2 12.6a8.5 8.5 0 019.6 0"/><path d="M10 16.2a4 4 0 014 0"/><circle cx="12" cy="19.2" r="0.9" fill="currentColor" stroke="none"/>',
    "MON": '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M6 11h3l1.5-3 2 6 1.5-3H18"/>',
    "SEC": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9.2 12.2l1.9 1.9 3.7-3.7"/>',
    "SCL": '<path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5"/>',
    "LOCK": '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 018 0v3"/><circle cx="12" cy="15" r="1.4" fill="currentColor" stroke="none"/>',
    "CARD": '<rect x="3" y="5" width="18" height="14" rx="2"/><rect x="6" y="9" width="4" height="3" rx="0.6"/><path d="M6 15h5M6 17h3"/>',
    "CMP": '<path d="M9 2v5M15 2v5M7 7h10v3a5 5 0 01-10 0z"/><path d="M12 15v3M9 21h6"/>',
    "LOG": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 3h6v3H9z"/><path d="M9 11h6M9 14h6M9 17h4"/>',
    "ZON": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/><rect x="9" y="9" width="6" height="6" fill="currentColor" stroke="none" opacity="0.15"/>',
    "MIG": '<rect x="2" y="8" width="6" height="8" rx="1"/><rect x="16" y="8" width="6" height="8" rx="1"/><path d="M9 12h6M12.5 9.5L15 12l-2.5 2.5"/>',
}


def service_icon(code):
    inner = _SERVICE_ICON_PATHS.get(code, "")
    svg = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" focusable="false">{inner}</svg>'
    )
    return Markup(f'<span class="service-icon">{svg}</span>')


@app.context_processor
def inject_globals():
    # Intentionally shadows Flask's own url_for inside Jinja rendering --
    # templates never call the real flask.url_for, only this simpler one
    # keyed by PAGES id. Python code can still use flask.url_for normally.
    return {
        "url_for": url_for_page,
        "asset": asset,
        "service_icon": service_icon,
        "SITE_URL": SITE_URL,
        "ASSET_VERSION": ASSET_VERSION,
    }


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
