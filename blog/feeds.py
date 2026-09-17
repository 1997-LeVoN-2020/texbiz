"""RSS блога: /feed/ и /blog/feed/. На /feed/ уже стучались до того, как он появился."""
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import Article


class ArticleFeed(Feed):
    title = "Блог ТЕХБИЗ — автоматизация отелей"
    description = "Статьи об автоматизации гостиниц: 1С:Отель, онлайн-кассы, серверы, замковые системы, каналы продаж."
    language = "ru"

    def link(self):
        return reverse("blog:index")

    def items(self):
        return Article.objects.published()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_author_name(self, item):
        return settings.SITE_NAME
