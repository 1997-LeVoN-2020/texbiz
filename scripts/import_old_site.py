"""
Перенос контента старого Flask-сайта (reference-old-site/) в фикстуры Django.

Запуск из корня проекта:

    python scripts/import_old_site.py

Результат:
    web/icons.py                 — контурные значки из старого app.py
    web/fixtures/services.json   — 8 услуг (4 со страницей, 4 без)
    web/fixtures/solutions.json  — 4 решения по формату объекта
    blog/fixtures/articles.json  — 12 статей

Скрипт одноразовый и повторяемый: после переноса содержимое живёт в фикстурах
и в базе, а reference-old-site/ можно удалить.
"""
import ast
import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / "reference-old-site"
PAGES_DIR = OLD / "src" / "templates" / "pages"

# id страницы в старом app.py -> slug услуги (адрес сохраняется)
SERVICE_IDS = {
    "svc_1c": "1c-avtomatizaciya-otelya",
    "svc_kassy": "onlain-kassy-dlya-gostinicy",
    "svc_servers": "nastroika-serverov-otelya",
    "svc_locks": "integraciya-zamkovyh-sistem",
}

# Карточки старой главной без своей страницы: заголовок -> slug
EXTRA_SERVICES = {
    "Поддержка и сопровождение": "podderzhka-i-soprovozhdenie",
    "Интеграция каналов продаж": "integraciya-kanalov-prodazh",
    "Миграция и запуск без простоя": "migraciya-bez-prostoya",
    "Обучение персонала": "obuchenie-personala",
}

# Решения по формату: ключ вкладки старой главной -> (slug, id статьи по теме)
SOLUTIONS = {
    "hotel": ("otel", "blog_1c"),
    "mini": ("mini-otel", "blog_mini_hotel"),
    "apart": ("apartamenty", "blog_apartments"),
    "chain": ("set-otelej", "blog_chain"),
}

# Якорные ссылки на старую главную -> страницы нового сайта
ANCHORS = {
    ("home", "services"): "/uslugi/",
    ("home", "contacts"): "/kontakty/",
    ("home", "cases"): "/",
    ("home", "top"): "/",
    ("home", "booking-engine"): "/booking/",
    ("home", "segments"): "/resheniya/",
    ("home", "support"): "/uslugi/#support",
}

URLFOR_RE = re.compile(r"\{\{\s*url_for\(\s*'(\w+)'(?:\s*,\s*anchor\s*=\s*'([\w-]+)')?\s*\)\s*\}\}")
ICON_RE = re.compile(r"\{\{\s*service_icon\('(\w+)'\)\s*\}\}")
CARD_RE = re.compile(
    r"<article class=\"card reveal\">\s*(?:\{\{\s*service_icon\('(\w+)'\)\s*\}\})?\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</article>",
    re.S,
)
FAQ_RE = re.compile(r"<details class=\"faq-item reveal\">\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>", re.S)


def load_app_py():
    tree = ast.parse((OLD / "app.py").read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("PAGES", "_SERVICE_ICON_PATHS"):
                found[name] = ast.literal_eval(node.value)
    return found["PAGES"], found["_SERVICE_ICON_PATHS"]


def clean(text):
    return " ".join(text.split())


def strip_tags(text):
    return clean(re.sub(r"<[^>]+>", "", text))


def resolve_urls(html, urls):
    def repl(m):
        page_id, anchor = m.group(1), m.group(2)
        if anchor:
            if (page_id, anchor) in ANCHORS:
                return ANCHORS[(page_id, anchor)]
            return urls[page_id] + "#" + anchor
        return urls[page_id]

    return URLFOR_RE.sub(repl, html)


def tidy(html):
    html = html.replace(' class="reveal"', "").replace(" reveal\"", "\"")
    html = re.sub(r"\n{3,}", "\n\n", html)
    return textwrap.dedent(html).strip() + "\n"


def parse_service_page(slug, urls):
    html = (PAGES_DIR / f"{slug}.html").read_text(encoding="utf-8")
    h1 = clean(re.search(r'<h1 id="hero-title">(.*?)</h1>', html, re.S).group(1))
    lead = clean(re.search(r'<p class="lead">(.*?)</p>', html, re.S).group(1))

    what = re.search(r'<section class="section" id="what".*?</section>', html, re.S).group(0)
    what_h2 = clean(re.search(r'<h2 id="what-title">(.*?)</h2>', what, re.S).group(1))
    features = [(clean(t), clean(p)) for _icon, t, p in CARD_RE.findall(what)]

    faq = re.search(r'<section class="section" id="faq".*?</section>', html, re.S).group(0)
    faq_h2 = clean(re.search(r'<h2 id="faq-title">(.*?)</h2>', faq, re.S).group(1))
    faq_items = [(clean(q), clean(a)) for q, a in FAQ_RE.findall(faq)]

    parts = [f"<h2>{what_h2}</h2>", '<div class="features">']
    for title, text in features:
        parts.append(f"  <div class=\"feature\">\n    <h3>{title}</h3>\n    <p>{text}</p>\n  </div>")
    parts.append("</div>")
    parts.append(f"<h2>{faq_h2}</h2>")
    for q, a in faq_items:
        parts.append(f"<details class=\"faq-item\">\n  <summary>{q}</summary>\n  <p>{a}</p>\n</details>")
    body = resolve_urls("\n".join(parts), urls) + "\n"
    return h1, lead, body, len(features), len(faq_items)


def parse_home_cards(urls):
    """Карточки услуг старой главной: (значок, заголовок, id страницы или None, текст)."""
    html = (PAGES_DIR / "index.html").read_text(encoding="utf-8")
    section = re.search(r'<section class="section" id="services".*?</section>', html, re.S).group(0)
    cards = []
    for icon, h3, text in CARD_RE.findall(section):
        link = re.search(r"url_for\('(\w+)'\)", h3)
        cards.append((icon, strip_tags(h3), link.group(1) if link else None, clean(text)))
    return cards


def parse_solutions(pages_by_id, urls):
    html = (PAGES_DIR / "index.html").read_text(encoding="utf-8")
    panels = re.findall(
        r'<article class="segment-panel[^"]*" data-segment-panel="(\w+)">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>',
        html,
        re.S,
    )
    out = []
    for order, (key, title, text) in enumerate(panels, start=1):
        slug, article_id = SOLUTIONS[key]
        article = pages_by_id[article_id]
        body = (
            f"<p>{clean(text)}</p>\n"
            f"<p class=\"more\"><a href=\"{urls[article_id]}\">{article['og_title']}</a></p>\n"
        )
        out.append({"model": "web.solution", "pk": order, "fields": {
            "title": clean(title), "slug": slug, "body": body, "order": order, "is_published": True,
        }})
    return out


def parse_blog_index(urls):
    html = (PAGES_DIR / "blog" / "index.html").read_text(encoding="utf-8")
    excerpts = {}
    for page_id, text in re.findall(r"<h3><a href=\"\{\{ url_for\('(\w+)'\) \}\}\">.*?</a></h3>\s*<p>(.*?)</p>", html, re.S):
        excerpts[page_id] = clean(text)
    return excerpts


def parse_article(page, urls):
    html = (PAGES_DIR / page["template"].removeprefix("pages/")).read_text(encoding="utf-8")
    date = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', html).group(1)
    h1 = clean(re.search(r'<h1 id="article-title">(.*?)</h1>', html, re.S).group(1))
    container = re.search(r'<div class="container legal-content">(.*?)</div>\s*</section>', html, re.S).group(1)
    container = re.sub(r'<p class="eyebrow">.*?</p>\s*', "", container, count=1, flags=re.S)
    container = re.sub(r'<h1 id="article-title">.*?</h1>\s*', "", container, count=1, flags=re.S)
    container = container.replace('class="section-subtitle"', 'class="lead"')
    body = tidy(resolve_urls(container, urls))
    return h1, date, body


def main():
    pages, icon_paths = load_app_py()
    pages_by_id = {p["id"]: p for p in pages}
    urls = {p["id"]: "/" + p["url_path"] for p in pages}

    # --- Значки --------------------------------------------------------------
    icons_py = ['"""Контурные значки 24×24 (только path-данные). Перенесены со старого сайта скриптом scripts/import_old_site.py."""', "", "ICON_PATHS = {"]
    for code, path in icon_paths.items():
        icons_py.append(f"    {code!r}: {path!r},")
    icons_py += ["}", "", "ICON_CHOICES = [(code, code) for code in ICON_PATHS]", ""]
    (ROOT / "web" / "icons.py").write_text("\n".join(icons_py), encoding="utf-8")

    # --- Услуги --------------------------------------------------------------
    cards = parse_home_cards(urls)
    services = []
    order = 0
    for icon, title, link_id, text in cards:
        if link_id == "booking":
            continue  # модуль бронирования — продукт, у него своя страница и шаблон
        order += 1
        if link_id in SERVICE_IDS:
            slug = SERVICE_IDS[link_id]
            page = pages_by_id[link_id]
            h1, lead, body, n_feat, n_faq = parse_service_page(slug, urls)
            services.append({"model": "web.service", "pk": order, "fields": {
                "title": h1, "slug": slug, "icon": icon, "summary": text, "lead": lead, "body": body,
                "meta_title": page["title"], "meta_description": page["description"],
                "order": order, "is_published": True,
            }})
            print(f"услуга {slug}: {n_feat} пунктов, {n_faq} вопросов")
        else:
            slug = EXTRA_SERVICES[title]
            services.append({"model": "web.service", "pk": order, "fields": {
                "title": title, "slug": slug, "icon": icon, "summary": text, "lead": "", "body": "",
                "meta_title": "", "meta_description": "", "order": order, "is_published": True,
            }})
            print(f"услуга {slug}: без страницы")

    # --- Решения -------------------------------------------------------------
    solutions = parse_solutions(pages_by_id, urls)
    print(f"решений: {len(solutions)}")

    # --- Статьи --------------------------------------------------------------
    excerpts = parse_blog_index(urls)
    articles = []
    pk = 0
    for page in pages:
        if not page["id"].startswith("blog_") or page["id"] == "blog_index":
            continue
        pk += 1
        h1, date, body = parse_article(page, urls)
        slug = page["url_path"].removeprefix("blog/").rstrip("/")
        articles.append({"model": "blog.article", "pk": pk, "fields": {
            "title": h1, "slug": slug, "excerpt": excerpts[page["id"]], "body": body,
            "published_at": f"{date}T09:00:00+03:00",
            "meta_title": page["title"], "meta_description": page["description"],
            "is_published": True,
        }})
        print(f"статья {slug}: {date}, {len(body)} символов")

    # --- Проверка: в текстах не осталось Jinja ---------------------------------
    problems = []
    for fx in services + solutions + articles:
        for key in ("body", "lead", "summary"):
            value = fx["fields"].get(key, "")
            if "{{" in value or "{%" in value:
                problems.append((fx["model"], fx["fields"].get("slug"), key))
    if problems:
        print("ОШИБКА: остались куски Jinja:", problems)
        sys.exit(1)

    hrefs = set()
    for fx in services + solutions + articles:
        hrefs.update(re.findall(r'href="([^"]+)"', fx["fields"].get("body", "")))
    print("ссылки в текстах:", sorted(hrefs))

    def dump(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dump(ROOT / "web" / "fixtures" / "services.json", services)
    dump(ROOT / "web" / "fixtures" / "solutions.json", solutions)
    dump(ROOT / "blog" / "fixtures" / "articles.json", articles)
    print("готово: services.json, solutions.json, articles.json, web/icons.py")


if __name__ == "__main__":
    main()
