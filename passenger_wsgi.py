"""
Точка входа для Passenger (ISPmanager на reg.ru).

Панель запускает приложение современным Python (проверено на сервере:
/opt/python/python-3.14/bin/python), поэтому переключать интерпретатор не надо
и НЕЛЬЗЯ. Ранняя версия этого файла делала os.execl на python из окружения —
Passenger от этого отдавал 500 на каждой странице, не записывая в журнал ни
строчки: перезапуск интерпретатора рвёт его протокол связи с приложением.

Правильный приём взят из соседнего проекта booking-engine, который работает на
этом же сервере: каталог пакетов виртуального окружения добавляется в пути
поиска, а интерпретатор остаётся тот, которым запустила панель.
"""
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
# ~/www/<домен> → на два уровня вверх это домашний каталог, рядом с которым
# лежит виртуальное окружение.
DATA_DIR = os.path.normpath(os.path.join(PROJECT_DIR, "..", ".."))

MIN_PYTHON = (3, 12)  # требование Django 6.1

if sys.version_info[:2] < MIN_PYTHON:
    raise RuntimeError(
        "Панель должна запускать приложение на Python "
        "{}.{} или новее, а запустила {}.{}. Поменяйте версию в настройках "
        "Python-приложения в ISPmanager.".format(
            MIN_PYTHON[0], MIN_PYTHON[1], sys.version_info[0], sys.version_info[1]
        )
    )

PYTHON_TAG = "python{}.{}".format(sys.version_info[0], sys.version_info[1])

CANDIDATES = [
    os.environ.get("TEXBIZ_VENV", ""),
    # Рядом с каталогом сайта: ~/www/<домен> лежит на два уровня ниже дома.
    os.path.join(DATA_DIR, "texbiz-django"),
    # То же место, но через домашний каталог: работает и когда проект лежит
    # не на своём обычном уровне вложенности, например при проверке из /tmp.
    os.path.expanduser(os.path.join("~", "texbiz-django")),
    os.path.join(PROJECT_DIR, ".venv"),
]

site_packages = ""
for candidate in CANDIDATES:
    if not candidate:
        continue
    path = os.path.join(candidate, "lib", PYTHON_TAG, "site-packages")
    if os.path.isdir(path):
        site_packages = path
        break

if not site_packages:
    raise RuntimeError(
        "Не найдено окружение с зависимостями для {}. Искали в: {}. "
        "Создать: /opt/python/python-3.14/bin/python3 -m venv ~/texbiz-django".format(
            PYTHON_TAG, ", ".join(c for c in CANDIDATES if c)
        )
    )

sys.path.insert(0, site_packages)
sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
