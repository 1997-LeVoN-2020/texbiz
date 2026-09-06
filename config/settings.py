"""
Настройки сайта ТЕХБИЗ.

Всё, что зависит от окружения, берётся из переменных окружения или из файла
.env в корне проекта (образец — .env.example). Секретов в коде нет.

Админка намеренно не подключена: приложение django.contrib.admin установлено,
но адрес /admin/ не зарегистрирован (см. config/urls.py). Включается одной
правкой, когда понадобится.
"""
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Подмена системного SQLite обязана произойти до того, как Django импортирует
# свой драйвер, поэтому стоит здесь, в самом начале настроек. Подробности —
# в config/sqlite_compat.py.
from config import sqlite_compat  # noqa: E402

SQLITE_CONNECTION_CLASS = sqlite_compat.install()

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Минимальный разбор .env: KEY=value, строки с # пропускаются, кавычки по краям снимаются."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Базовое ---------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", False)

_DEV_SECRET = "dev-only-insecure-key"
SECRET_KEY = env("DJANGO_SECRET_KEY", _DEV_SECRET)
if not DEBUG and SECRET_KEY == _DEV_SECRET:
    raise ImproperlyConfigured("Задайте DJANGO_SECRET_KEY в .env для боевого режима")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "tex-biz.ru,www.tex-biz.ru,localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "https://tex-biz.ru,https://www.tex-biz.ru")

INSTALLED_APPS = [
    "django.contrib.admin",  # установлено, адрес не подключён — задел под админку
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "web",
    "blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- База данных -----------------------------------------------------------

DATA_DIR = Path(env("DJANGO_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# По умолчанию SQLite: сайту с формой заявок большего не нужно, а файл базы
# проще резервировать. Если хостинг не даёт достаточно свежий SQLite,
# заполните DB_NAME и остальное в .env — тогда используется MySQL, как в
# соседнем проекте booking-engine на этом же сервере. Менять код для этого
# не требуется.
if env("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER", ""),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", ""),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    _sqlite_options = {
        "transaction_mode": "IMMEDIATE",
        "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;",
    }
    # Класс соединения с заплаткой нужен только там, где подменён SQLite.
    if SQLITE_CONNECTION_CLASS is not None:
        _sqlite_options["factory"] = SQLITE_CONNECTION_CLASS

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DATA_DIR / "db.sqlite3",
            "OPTIONS": _sqlite_options,
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Язык и время ----------------------------------------------------------

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# --- Статика и медиа -------------------------------------------------------
# public/ — каталог, который веб-сервер (Passenger) отдаёт напрямую.

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "public" / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "public" / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

# --- Кэш (лимит заявок по IP) ----------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "texbiz",
    }
}

# --- Сайт и контакты -------------------------------------------------------

SITE_URL = env("SITE_URL", "https://tex-biz.ru").rstrip("/")
SITE_NAME = "ТЕХБИЗ"
SITE_TAGLINE = "технологии для бизнеса"

CONTACT_PHONE = "+7 938 511-13-31"
CONTACT_PHONE_HREF = "tel:+79385111331"
CONTACT_EMAIL = "info@tex-biz.ru"
CONTACT_GEOGRAPHY = "Работаем по всей России"

LEGAL_NAME = "ИП Арушанян Левон Гарникович"
LEGAL_INN = "230123783003"
LEGAL_CITY = "г. Анапа"

YANDEX_METRIKA_ID = env("YANDEX_METRIKA_ID", "110630521")

BOOKING_DEMO_URL = env("BOOKING_DEMO_URL", "https://demo.booking-engine.ru/")

# --- Заявки ----------------------------------------------------------------

LEAD_NOTIFY_EMAILS = env_list("LEAD_NOTIFY_EMAILS", CONTACT_EMAIL)
LEAD_MIN_FILL_SECONDS = 3  # быстрее человек форму не заполнит
LEAD_RATE_LIMIT = 5  # заявок с одного IP…
LEAD_RATE_WINDOW = 600  # …за столько секунд

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", "")

# --- Почта -----------------------------------------------------------------

EMAIL_HOST = env("SMTP_HOST", "")
EMAIL_PORT = int(env("SMTP_PORT", "465"))
EMAIL_HOST_USER = env("SMTP_USER", "")
EMAIL_HOST_PASSWORD = env("SMTP_PASSWORD", "")
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_USE_TLS = EMAIL_PORT in (587, 25) and bool(EMAIL_HOST_USER)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env("MAIL_FROM", "noreply@tex-biz.ru")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Без настроенного SMTP письма печатаются в консоль — удобно в разработке
# и безопасно на сервере: заявка всё равно сохраняется в базе.
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend"
)

# --- Безопасность ----------------------------------------------------------
# Редирект на HTTPS выполняет ISPmanager, а не Django (иначе за прокси reg.ru
# получается бесконечный редирект). Django лишь доверяет заголовку прокси.

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Сайт себя нигде во фрейм не вставляет, поэтому DENY, а не SAMEORIGIN.
X_FRAME_OPTIONS = "DENY"

# HSTS начинается с часа: если что-то пойдёт не так с сертификатом, ошибка
# продержится час, а не год. Поднимать до 31536000 после того, как сайт
# отработает на HTTPS без нареканий.
SECURE_HSTS_SECONDS = 0 if DEBUG else int(env("DJANGO_HSTS_SECONDS", "3600"))

# Выключено намеренно. Заголовок с includeSubDomains заставляет браузер год
# требовать HTTPS от ВСЕХ поддоменов tex-biz.ru, включая те, о которых мы не
# знаем. Поддомен без действующего сертификата после этого перестаёт
# открываться, и откатить это нельзя: заголовок уже закэширован у посетителя.
# Включать, только когда точно известен список поддоменов и у каждого есть
# сертификат.
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = False

# W008: редирект на HTTPS делает ISPmanager, а не Django — за прокси reg.ru
#       собственный редирект даёт бесконечный цикл.
# W021: в preload-список не подаёмся, это одностороннее решение.
SILENCED_SYSTEM_CHECKS = ["security.W008", "security.W021"]

# --- Логи ------------------------------------------------------------------

LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "std": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "std"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "site.log"),
            "maxBytes": 2_000_000,
            "backupCount": 3,
            "encoding": "utf-8",
            "formatter": "std",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
    "loggers": {
        "django.request": {"level": "WARNING"},
    },
}
