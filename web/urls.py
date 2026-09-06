from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("uslugi/", views.services_index, name="services"),
    path("resheniya/", views.solutions, name="solutions"),
    path("booking/", views.booking, name="booking"),
    path("kontakty/", views.contacts, name="contacts"),
    path("privacy/", views.privacy, name="privacy"),
    path("spasibo/", views.thanks, name="thanks"),
    path("send/", views.lead_submit, name="lead_submit"),
    path("robots.txt", views.robots_txt, name="robots"),
    # Страницы услуг живут в корне, как на старом сайте: /1c-avtomatizaciya-otelya/
    path("<slug:slug>/", views.service_detail, name="service"),
]
