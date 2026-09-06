"""Теги шаблонов: значки услуг и подпись даты."""
from django import template
from django.utils.safestring import mark_safe

from web.icons import ICON_PATHS

register = template.Library()

MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


@register.simple_tag
def icon(code):
    """Контурный значок 24×24 по коду из web/icons.py. Цвет — currentColor."""
    inner = ICON_PATHS.get(code, ICON_PATHS["OPS"])
    return mark_safe(
        '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" focusable="false">{inner}</svg>'
    )


@register.filter
def ru_date(value):
    """7 июля 2026 — без зависимости от локали сервера."""
    if not value:
        return ""
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"
