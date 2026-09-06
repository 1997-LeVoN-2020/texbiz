"""Константы сайта, доступные во всех шаблонах как ``site``."""
import datetime

from django.conf import settings


def site(request):
    return {
        "site": {
            "url": settings.SITE_URL,
            "name": settings.SITE_NAME,
            "tagline": settings.SITE_TAGLINE,
            "phone": settings.CONTACT_PHONE,
            "phone_href": settings.CONTACT_PHONE_HREF,
            "email": settings.CONTACT_EMAIL,
            "geography": settings.CONTACT_GEOGRAPHY,
            "legal_name": settings.LEGAL_NAME,
            "legal_inn": settings.LEGAL_INN,
            "legal_city": settings.LEGAL_CITY,
            "metrika_id": settings.YANDEX_METRIKA_ID,
            "booking_demo": settings.BOOKING_DEMO_URL,
            "year": datetime.date.today().year,
            "debug": settings.DEBUG,
        }
    }
