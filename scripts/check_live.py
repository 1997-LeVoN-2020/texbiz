"""
Приёмка выложенного сайта. Проверяет живой домен снаружи, как это делает
посетитель и поисковый робот.

Запуск сразу после выкладки:

    python scripts/check_live.py
    python scripts/check_live.py https://tex-biz.ru

Зависимостей нет, виртуальное окружение не нужно. Код возврата 1, если есть
ошибки. Пункты с пометкой «критично» означают утечку или неработающий приём
заявок — публиковать сайт с ними нельзя.
"""
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT = "https://tex-biz.ru"
UA = "texbiz-deploy-check"
TIMEOUT = 20

PAGES = [
    "/",
    "/uslugi/",
    "/resheniya/",
    "/booking/",
    "/kontakty/",
    "/privacy/",
    "/blog/",
    "/1c-avtomatizaciya-otelya/",
    "/onlain-kassy-dlya-gostinicy/",
    "/nastroika-serverov-otelya/",
    "/integraciya-zamkovyh-sistem/",
    "/blog/1c-avtomatizaciya-otelya-s-chego-nachat/",
    "/sitemap.xml",
    "/robots.txt",
]

# Файлы, которые не должны отдаваться никогда: база с заявками, пароли, код.
MUST_NOT_BE_SERVED = [
    "/data/db.sqlite3",
    "/data/logs/site.log",
    "/.env",
    "/config/settings.py",
    "/manage.py",
    "/db.sqlite3",
    "/web/fixtures/services.json",
]

errors = []
warnings = []
notes = []


def fetch(url, redirect=True, method="GET"):
    """Возвращает (код, заголовки, тело). Ошибки HTTP — тоже ответ, а не исключение."""

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener() if redirect else urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            return response.status, dict(response.headers), response.read(200_000)
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read(20_000)
    except Exception as exc:  # сеть, DNS, сертификат
        return None, {}, str(exc).encode()


def check_pages(base):
    print("Страницы")
    for path in PAGES:
        code, _, body = fetch(base + path)
        if code == 200:
            print(f"  ок   200  {path}  ({len(body)} байт)")
        else:
            print(f"  ОШИБ {code}  {path}")
            errors.append(f"{path} отдаёт {code}, ожидалось 200")


def check_not_served(base):
    print("\nЗакрытые файлы (критично)")
    for path in MUST_NOT_BE_SERVED:
        code, _, body = fetch(base + path)
        if code in (403, 404):
            print(f"  ок   {code}  {path}")
        elif code == 200:
            print(f"  УТЕЧКА 200 {path}  ({len(body)} байт)")
            errors.append(f"КРИТИЧНО: {path} отдаётся файлом. Проверьте, что .htaccess загрузился на сервер")
        else:
            print(f"  ?    {code}  {path}")
            warnings.append(f"{path} отдаёт {code}: проверьте вручную")


def check_redirects(base):
    print("\nПеренаправления")
    host = urlparse(base).netloc

    code, headers, _ = fetch(f"http://{host}/", redirect=False)
    location = headers.get("Location", "")
    if code in (301, 302, 307, 308) and location.startswith("https://"):
        print(f"  ок   {code}  http ведёт на {location}")
    else:
        print(f"  ОШИБ {code}  http не ведёт на https (Location: {location or 'нет'})")
        errors.append("Нет перенаправления с http на https. Включается галочкой в ISPmanager")

    if not host.startswith("www."):
        code, headers, _ = fetch(f"https://www.{host}/", redirect=False)
        location = headers.get("Location", "")
        if code in (301, 302, 307, 308) and "//www." not in location:
            print(f"  ок   {code}  www ведёт на {location}")
        else:
            print(f"  ?    {code}  www не перенаправляется (Location: {location or 'нет'})")
            warnings.append("www не перенаправляется на домен без www")


def check_static(base):
    print("\nСтатика")
    code, _, body = fetch(base + "/")
    if code != 200:
        errors.append("Главная не открылась, статику проверить не удалось")
        return
    html = body.decode("utf-8", "replace")
    import re

    hrefs = re.findall(r'href="(/static/[^"]+\.css)"', html) + re.findall(r'src="(/static/[^"]+\.js)"', html)
    if not hrefs:
        errors.append("На главной нет ссылок на собственную статику")
        return
    for href in dict.fromkeys(hrefs):
        code, headers, body = fetch(base + href)
        ctype = headers.get("Content-Type", "")
        if code == 200 and ("css" in ctype or "javascript" in ctype):
            print(f"  ок   200  {href}  ({ctype.split(';')[0]}, {len(body)} байт)")
        else:
            print(f"  ОШИБ {code}  {href}  ({ctype})")
            errors.append(f"{href} не отдаётся как статика: сайт откроется без стилей. Проверьте переброску /static/ в .htaccess и collectstatic")


def check_headers_and_debug(base):
    print("\nЗаголовки и режим")
    code, headers, body = fetch(base + "/")
    html = body.decode("utf-8", "replace")

    for header, expected in [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", None),
        ("Strict-Transport-Security", None),
    ]:
        value = headers.get(header)
        if value and (expected is None or expected.lower() in value.lower()):
            print(f"  ок        {header}: {value}")
        else:
            print(f"  нет       {header}: {value or 'отсутствует'}")
            warnings.append(f"Заголовок {header} не выставлен или отличается: {value or 'нет'}")

    if "Traceback" in html or "DJANGO_SETTINGS_MODULE" in html:
        errors.append("КРИТИЧНО: на странице видна отладочная информация. DJANGO_DEBUG должен быть выключен")
    else:
        print("  ок        отладочной информации на странице нет")

    code, _, body = fetch(base + "/takoy-stranicy-net/")
    if code == 404 and "ТЕХБИЗ" in body.decode("utf-8", "replace"):
        print("  ок   404  своя страница «не найдено»")
    else:
        warnings.append(f"Несуществующий адрес отдаёт {code}, ожидалась своя страница 404")


def check_form(base):
    print("\nФорма заявки")
    code, _, body = fetch(base + "/kontakty/")
    html = body.decode("utf-8", "replace")
    if code != 200:
        errors.append("Страница контактов не открылась")
        return
    checks = [
        ("csrfmiddlewaretoken", "защита CSRF на месте"),
        ('action="/send/"', "форма ведёт на обработчик"),
        ('name="consent"', "отметка согласия на обработку данных"),
        ('name="website"', "ловушка для ботов"),
    ]
    for needle, label in checks:
        if needle in html:
            print(f"  ок        {label}")
        else:
            print(f"  ОШИБ      {label} — не найдено")
            errors.append(f"На форме нет: {label}")
    notes.append("Отправьте тестовую заявку руками и убедитесь, что письмо дошло: автоматически это не проверить")


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).rstrip("/")
    print(f"Проверяю {base}\n")

    code, _, body = fetch(base + "/")
    if code is None:
        print(f"Сайт недоступен: {body.decode('utf-8', 'replace')}")
        return 1

    check_pages(base)
    check_not_served(base)
    check_redirects(base)
    check_static(base)
    check_headers_and_debug(base)
    check_form(base)

    print()
    if notes:
        print("Проверить руками:")
        for line in notes:
            print("  •", line)
        print()
    if warnings:
        print(f"Предупреждения ({len(warnings)}):")
        for line in warnings:
            print("  ~", line)
        print()
    if errors:
        print(f"Ошибки ({len(errors)}):")
        for line in errors:
            print("  !", line)
        return 1

    print("Ошибок нет, сайт можно считать выложенным.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
