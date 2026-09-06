"""
Совместимость со старым SQLite на хостинге reg.ru.

Django 6.1 требует SQLite 3.37 и новее, а системный на сервере — 3.26.
Пакет pysqlite3-binary приносит с собой 3.51, и этот модуль подставляет его
вместо системного.

Одна тонкость. Django спрашивает у соединения предельное число параметров
в запросе через метод `getlimit`, который появился в стандартном модуле
Python 3.11. В pysqlite3 его нет, и без заплатки падает `migrate` и всё, что
делает массовую вставку. Заплатка добавляет метод через подкласс соединения:
Django передаёт его в драйвер параметром `factory` из OPTIONS.

Значение намеренно занижено до 999 — это старый предел SQLite. Django по нему
дробит массовые вставки на части: заниженное значение делает больше частей,
но работает всегда. Завышенное дало бы ошибку «слишком много параметров».

Модуль ничего не делает, если pysqlite3 не установлен: на машине разработчика
и на нормальном хостинге используется системный SQLite.
"""
import sys

# Коды из sqlite3.h. Нужен только предел на число параметров, остальные Django
# не спрашивает; для незнакомых кодов отдаём консервативное значение.
SQLITE_LIMIT_VARIABLE_NUMBER = 9
CONSERVATIVE_LIMITS = {SQLITE_LIMIT_VARIABLE_NUMBER: 999}


def install():
    """Подменяет системный sqlite3. Возвращает класс соединения или None."""
    try:
        import pysqlite3  # noqa: F401
        import pysqlite3.dbapi2 as dbapi2
    except ImportError:
        return None

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    sys.modules["sqlite3.dbapi2"] = dbapi2

    if hasattr(dbapi2.Connection, "getlimit"):
        return None  # заплатка не нужна, метод уже есть

    class CompatConnection(dbapi2.Connection):
        def getlimit(self, category):
            return CONSERVATIVE_LIMITS.get(category, 999)

    return CompatConnection
