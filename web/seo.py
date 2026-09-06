"""Метаданные страниц и микроразметка JSON-LD."""
import json

from django.conf import settings
from django.utils.safestring import mark_safe

ROBOTS_DEFAULT = "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"


def page_meta(request, *, title, description, og_type="website", noindex=False, og_title=None, og_description=None):
    """Единый набор данных для <head>: title, description, canonical, OG, robots."""
    return {
        "title": title,
        "description": description,
        "canonical": settings.SITE_URL + request.path,
        "og_type": og_type,
        "og_title": og_title or title,
        "og_description": og_description or description,
        "robots": "noindex, follow" if noindex else ROBOTS_DEFAULT,
    }


def jsonld(data):
    """JSON-LD как строка для вставки в <script>. «</» экранируется, чтобы не закрыть тег."""
    text = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return mark_safe(text)


def organization():
    return {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": settings.SITE_NAME,
        "alternateName": "Технологии для бизнеса",
        "legalName": settings.LEGAL_NAME,
        "taxID": settings.LEGAL_INN,
        "address": {"@type": "PostalAddress", "addressLocality": "Анапа", "addressCountry": "RU"},
        "url": settings.SITE_URL + "/",
        "description": "Комплексная автоматизация гостиниц и отелей: внедрение 1С, настройка онлайн-касс, серверной инфраструктуры и замковых систем.",
        "telephone": settings.CONTACT_PHONE_HREF.replace("tel:", ""),
        "email": settings.CONTACT_EMAIL,
        "areaServed": "RU",
        "serviceType": [
            "Автоматизация 1С для отеля",
            "Настройка онлайн-касс",
            "Настройка серверов",
            "Интеграция замковых систем",
            "Модуль онлайн-бронирования",
        ],
    }


def faq_page(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in items
        ],
    }
