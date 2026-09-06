# ТЕХБИЗ — сайт tex-biz.ru

Сайт компании ТЕХБИЗ на Django 6.1: автоматизация отелей под ключ. Вёрстка на
HTML5, CSS и JavaScript без библиотек, дизайн по брендбуку от 05.09.2026.
Админка пока не подключена, но проект собран так, чтобы включить её одной правкой.

План работ с чек-листом и решениями по проекту: [docs/plan.md](docs/plan.md).

## Структура

```
manage.py
config/            настройки (settings.py читает .env), адреса, WSGI
web/               страницы, услуги, решения, заявки, sitemap, значки
  fixtures/        services.json, solutions.json — содержимое услуг и решений
  templatetags/    {% icon %} и фильтр ru_date
blog/              статьи (Article), fixtures/articles.json
templates/         base.html, includes/, web/, blog/
static/            css/main.css, js/main.js, img/ (знак, favicon, OG-картинка)
scripts/           import_old_site.py — перенос контента со старого сайта,
                   make_assets.py — растровые иконки и OG-картинка (нужен Pillow)
passenger_wsgi.py  точка входа для Passenger (ISPmanager)
data/              база SQLite и логи (создаётся автоматически, в git не попадает)
public/            статика после collectstatic (в git не попадает)
```

## Запуск локально

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env            # и поставить DJANGO_DEBUG=1
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py loaddata services solutions articles
.venv\Scripts\python manage.py runserver 127.0.0.1:8010
```

Сайт открывается на `http://127.0.0.1:8010/`. Без настроенного SMTP письма о заявках
печатаются в консоль, сами заявки всё равно сохраняются в базе.

## Содержимое

Услуги, решения и статьи хранятся в базе и загружаются из фикстур. Чтобы
поправить текст сейчас, без админки: изменить JSON в `web/fixtures/` или
`blog/fixtures/` и выполнить `manage.py loaddata <имя>`. Контакты и реквизиты
заданы один раз в `config/settings.py` и доступны во всех шаблонах как `site`.

## Заявки

`POST /send/` сохраняет заявку (`web.Lead`), отправляет письмо на адреса из
`LEAD_NOTIFY_EMAILS` и, если задан токен, дублирует в Telegram, затем ведёт на
`/spasibo/`. Антиспам: скрытое поле-ловушка, минимальное время заполнения,
лимит по IP. Форма работает и без JavaScript; с ним отправляется без
перезагрузки и показывает ошибки под полями.

## Как включить админку

1. В `config/urls.py` добавить `path("admin/", admin.site.urls)` первым правилом.
2. Создать `web/admin.py` и `blog/admin.py` с регистрацией моделей
   Service, Solution, Lead, Article.
3. `manage.py createsuperuser`.

## Деплой на reg.ru (ISPmanager, Passenger)

1. Загрузить проект в каталог домена (`git pull` или архив).
2. Создать Python-приложение в ISPmanager: путь `/`, Python 3.14, каталог проекта.
3. `.venv/bin/pip install -r requirements.txt` в окружении приложения.
4. Заполнить `.env` по образцу `.env.example`: секретный ключ, хосты, SMTP.
5. `manage.py migrate`, `manage.py loaddata services solutions articles`,
   `manage.py collectstatic`.
6. Перезапустить приложение в ISPmanager.
7. Проверить сайт, отправить тестовую заявку, убедиться, что письмо дошло.

Редирект на HTTPS включается галочкой в ISPmanager, а не в Django: за прокси
reg.ru собственный редирект даёт бесконечный цикл.
