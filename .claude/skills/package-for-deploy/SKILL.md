---
name: package-for-deploy
description: Собрать архив Django-сайта ТЕХБИЗ для загрузки на хостинг reg.ru с ISPmanager. Использовать когда просят «собери архив для деплоя», «подготовь zip для хостинга», «запакуй новую версию».
---

## Перед сборкой

Проверить, что всё готово: прогнать скилл `check-site` и агента `deploy-checklist`. Архив собирается из закоммиченного, поэтому сначала коммит.

## Команда

```
bash scripts/build_release.sh
```

Скрипт откажется работать при незакоммиченных изменениях и при существующем файле с тем же именем. Результат: `releases/texbiz-django-<дата>-<коммит>.zip`.

## Что попадает в архив

Собирается через `git archive` из `HEAD`, поэтому список того, что едет на сервер, задан одним местом — `.gitattributes`. Помечено `export-ignore` и в архив не попадает: `.claude/`, `docs/`, `scripts/`, `README.md`, `.gitignore`, `.gitattributes`.

Не попадает и не должно: `.env` (заполняется на сервере вручную), `data/` с базой и логами, `public/` со собранной статикой, `.venv/`, `reference-old-site/`.

## Дальше на сервере

1. Распаковать в каталог домена.
2. Заполнить `.env` по образцу `.env.example`: обязательно `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `SITE_URL`, настройки SMTP.
3. В окружении приложения:

```
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py loaddata services solutions articles
.venv/bin/python manage.py collectstatic --noinput
```

4. Перезапустить приложение в ISPmanager. **Без перезапуска Passenger продолжит отдавать старый код.**
5. Отправить тестовую заявку и убедиться, что письмо дошло.

## Грабли этого хостинга

Редирект на HTTPS включается галочкой в ISPmanager, а не в Django и не в `.htaccess`: за прокси reg.ru собственный редирект даёт `ERR_TOO_MANY_REDIRECTS`. На этом проекте так уже ломали сайт.

`passenger_wsgi.py` сам перезапускает процесс интерпретатором из `.venv`: путь `.venv/bin/python` на сервере, не `Scripts`. Если ISPmanager создал своё окружение в другом месте, поправить путь в файле.

В боевом режиме включается `ManifestStaticFilesStorage`: ссылка на несуществующий файл в шаблоне валит `collectstatic`. Это не поломка, а проверка — добавить недостающий файл.
