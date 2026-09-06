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

# Коды из sqlite3.h. Стандартный модуль Python объявляет их сам, pysqlite3 —
# нет, а Django обращается к ним по имени. Заводим весь набор, чтобы не
# возвращаться сюда из-за следующей недостающей константы.
LIMIT_CONSTANTS = {
    "SQLITE_LIMIT_LENGTH": 0,
    "SQLITE_LIMIT_SQL_LENGTH": 1,
    "SQLITE_LIMIT_COLUMN": 2,
    "SQLITE_LIMIT_EXPR_DEPTH": 3,
    "SQLITE_LIMIT_COMPOUND_SELECT": 4,
    "SQLITE_LIMIT_VDBE_OP": 5,
    "SQLITE_LIMIT_FUNCTION_ARG": 6,
    "SQLITE_LIMIT_ATTACHED": 7,
    "SQLITE_LIMIT_LIKE_PATTERN_LENGTH": 8,
    "SQLITE_LIMIT_VARIABLE_NUMBER": 9,
    "SQLITE_LIMIT_TRIGGER_DEPTH": 10,
    "SQLITE_LIMIT_WORKER_THREADS": 11,
}

# Значения по кодам: занижены намеренно, см. пояснение в описании модуля.
CONSERVATIVE_LIMITS = {LIMIT_CONSTANTS["SQLITE_LIMIT_VARIABLE_NUMBER"]: 999}


def install():
    """Подменяет системный sqlite3. Возвращает класс соединения или None."""
    try:
        import pysqlite3  # noqa: F401
        import pysqlite3.dbapi2 as dbapi2
    except ImportError:
        return None

    module = sys.modules.pop("pysqlite3")
    sys.modules["sqlite3"] = module
    sys.modules["sqlite3.dbapi2"] = dbapi2

    for name, code in LIMIT_CONSTANTS.items():
        for target in (module, dbapi2):
            if not hasattr(target, name):
                setattr(target, name, code)

    if hasattr(dbapi2.Connection, "getlimit"):
        return None  # заплатка не нужна, метод уже есть

    class CompatConnection(dbapi2.Connection):
        def getlimit(self, category):
            return CONSERVATIVE_LIMITS.get(category, 999)

    return CompatConnection
