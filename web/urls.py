from django.urls import path, register_converter

from . import views
from .models import Solution

app_name = "web"


class GroupConverter:
    """Код группы решений: /resheniya/finance/. Всё остальное после /resheniya/ — адрес решения."""

    regex = "|".join(Solution.Group.values)

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(GroupConverter, "group")

urlpatterns = [
    path("", views.home, name="home"),
    # Значок описан тегами в <head>, но браузеры и роботы всё равно дёргают
    # /favicon.ico в корне. Без этого правила каждый такой запрос — 404 в логе.
    path("favicon.ico", views.favicon, name="favicon"),
    path("uslugi/", views.services_index, name="services"),
    path("resheniya/", views.solutions, name="solutions"),
    path("resheniya/<group:group>/", views.solutions, name="solutions_group"),
    path("resheniya/<slug:slug>/", views.solution_detail, name="solution"),
    path("booking/", views.booking, name="booking"),
    path("kontakty/", views.contacts, name="contacts"),
    path("raschet/", views.estimate, name="estimate"),
    path("privacy/", views.privacy, name="privacy"),
    path("spasibo/", views.thanks, name="thanks"),
    path("send/", views.lead_submit, name="lead_submit"),
    path("robots.txt", views.robots_txt, name="robots"),
    # Страницы услуг живут в корне, как на старом сайте: /1c-avtomatizaciya-otelya/
    path("<slug:slug>/", views.service_detail, name="service"),
]
