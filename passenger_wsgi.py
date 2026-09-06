"""
Точка входа для Passenger (ISPmanager на reg.ru).

Passenger запускает системный Python; здесь процесс перезапускается
интерпретатором из виртуального окружения проекта, где установлен Django.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "bin", "python")

if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402
