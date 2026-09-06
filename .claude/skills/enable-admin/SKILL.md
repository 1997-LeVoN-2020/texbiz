---
name: enable-admin
description: Включить админку Django на сайте ТЕХБИЗ — зарегистрировать модели, подключить адрес, создать пользователя. Использовать когда просят «включи админку», «дай редактировать через панель», «хочу править тексты сам».
---

Сайт собран с заделом под админку: приложение `django.contrib.admin` уже стоит в `INSTALLED_APPS`, но адрес `/admin/` намеренно не подключён. Включение — три шага.

## 1. Адрес

В `config/urls.py` первым правилом:

```python
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    ...
]
```

Именно первым: последнее правило в `web/urls.py` — `<slug:slug>/`, оно перехватит любой адрес в корне.

Адрес стоит сделать неочевидным (не `/admin/`, а например `/panel-upravleniya/`) и вынести в переменную окружения: перебор паролей на `/admin/` идёт непрерывно.

## 2. Регистрация моделей

Создать `web/admin.py`:

```python
from django.contrib import admin

from .models import Lead, Service, Solution


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order", "is_published")
    list_editable = ("order", "is_published")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "phone", "object_type", "rooms_count", "status")
    list_filter = ("status", "created_at", "object_type")
    search_fields = ("name", "phone", "email", "message")
    date_hierarchy = "created_at"
    # Поля клиента только на чтение: историю обращения переписывать нельзя.
    readonly_fields = (
        "name", "phone", "email", "object_type", "rooms_count",
        "message", "source_page", "consent", "created_at",
    )
    fields = readonly_fields + ("status",)

    def has_add_permission(self, request):
        return False  # заявки создаёт только форма на сайте
```

И `blog/admin.py`:

```python
from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_published")
    list_filter = ("is_published", "published_at")
    search_fields = ("title", "excerpt", "body")
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title",)}
```

Слаг у опубликованной записи не должен меняться: адрес проиндексирован. Если это важно, добавить `slug` в `readonly_fields` для уже опубликованных записей.

## 3. Пользователь

```
.venv/Scripts/python manage.py createsuperuser
```

На сервере эту же команду выполнить в окружении приложения. Пароль владелец задаёт сам, в переписку и в файлы он не попадает.

## Что появится в панели

Услуги, решения, статьи и заявки. Тексты можно будет править прямо там, но фикстуры в репозитории при этом не обновляются: после правок в панели `loaddata` затрёт их обратно. Договориться с владельцем об одном источнике правды — либо фикстуры, либо панель.

## Что нужно доделать для картинок

Модели сейчас без полей изображений. Если понадобится загружать фото, добавить `ImageField`, поставить `Pillow` в окружение (в `.venv` его нет, только в системном Python), создать миграцию и настроить раздачу `MEDIA_ROOT` веб-сервером. Резервное копирование `public/media/` тогда обязательно наравне с базой.

## После включения

Проверить, что `/admin/` требует вход, что страницы сайта не сломались, и что `scripts/check_site.py` проходит.
