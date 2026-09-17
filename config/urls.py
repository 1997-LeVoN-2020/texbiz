"""
Адреса сайта.

Порядок важен: приложение web заканчивается правилом ``<slug>/`` для страниц
услуг (они живут в корне, как на старом сайте), поэтому панель, blog, RSS и
sitemap подключаются раньше.

Панель управления живёт по адресу из DJANGO_ADMIN_URL, а не по /admin/:
перебор паролей на /admin/ идёт непрерывно. Вход — суперпользователь:
``manage.py createsuperuser``.
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from blog.feeds import ArticleFeed
from web.sitemaps import SITEMAPS

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("blog/", include("blog.urls")),
    path("feed/", ArticleFeed(), name="feed"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("", include("web.urls")),
]

admin.site.site_header = "ТЕХБИЗ — панель управления"
admin.site.site_title = "ТЕХБИЗ"
admin.site.index_title = "Заявки и содержимое сайта"

handler404 = "web.views.not_found"
handler500 = "web.views.server_error"
