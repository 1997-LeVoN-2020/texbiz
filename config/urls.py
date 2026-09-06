"""
Адреса сайта.

Порядок важен: приложение web заканчивается правилом ``<slug>/`` для страниц
услуг (они живут в корне, как на старом сайте), поэтому blog и sitemap
подключаются раньше.

Админка не подключена намеренно. Чтобы включить:

    from django.contrib import admin
    urlpatterns.insert(0, path("admin/", admin.site.urls))

плюс зарегистрировать модели в web/admin.py и blog/admin.py и создать
суперпользователя: ``manage.py createsuperuser``.
"""
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from web.sitemaps import SITEMAPS

urlpatterns = [
    path("blog/", include("blog.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("", include("web.urls")),
]

handler404 = "web.views.not_found"
handler500 = "web.views.server_error"
