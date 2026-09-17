"""Панель управления: заявки — в работу, содержимое — посмотреть.

Тексты услуг, решений и статей живут в фикстурах репозитория, и каждая
выкладка загружает их заново (`loaddata` в scripts/deploy.sh). Правка в
панели пережила бы только до следующей выкладки, поэтому содержимое здесь
открыто на чтение. Чтобы править тексты в панели, нужно убрать `loaddata`
из выкладки и считать базу источником правды — это решение владельца.
"""
from django.contrib import admin

from .models import Lead, Service, Solution


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Service)
class ServiceAdmin(ReadOnlyAdmin):
    list_display = ("title", "slug", "order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "summary")


@admin.register(Solution)
class SolutionAdmin(ReadOnlyAdmin):
    list_display = ("title", "group", "slug", "order", "is_published")
    list_filter = ("group", "is_published")
    search_fields = ("title", "summary")


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
