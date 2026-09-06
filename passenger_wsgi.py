"""
Точка входа для Passenger (ISPmanager на reg.ru).

Passenger запускает приложение системным Python. На этом хостинге системный —
3.6, а Django 6.1 требует 3.12 и новее, поэтому процесс здесь перезапускается
интерпретатором из виртуального окружения.

Окружение вынесено за пределы каталога сайта: так его не задевает перенос
файлов с удалением лишнего при выкладке, и оно не отдаётся веб-сервером.
Путь можно задать переменной TEXBIZ_PYTHON в настройках приложения; иначе
проверяются известные места, первое существующее и берётся.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")

CANDIDATES = [
    os.environ.get("TEXBIZ_PYTHON"),
    # Боевой сервер: окружение на Python 3.14 рядом с каталогом сайта.
    os.path.join(HOME, "texbiz-django", "bin", "python"),
    # Локальная разработка.
    os.path.join(BASE_DIR, ".venv", "bin", "python"),
    os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe"),
]

for interpreter in CANDIDATES:
    if interpreter and os.path.exists(interpreter):
        if os.path.realpath(sys.executable) != os.path.realpath(interpreter):
            os.execl(interpreter, interpreter, *sys.argv)
        break

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402
