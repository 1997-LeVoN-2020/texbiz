"""sitemap.xml: статические страницы, услуги со своей страницей, решения и их группы, статьи."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Article

from .models import Service, Solution

# (имя адреса, приоритет, частота обновления)
STATIC_PAGES = [
    ("web:home", 1.0, "weekly"),
    ("web:services", 0.9, "monthly"),
    ("web:booking", 0.9, "weekly"),
    ("web:solutions", 0.8, "monthly"),
    ("blog:index", 0.7, "weekly"),
    ("web:contacts", 0.6, "yearly"),
]


class StaticSitemap(Sitemap):
    protocol = "https"

    def items(self):
        return STATIC_PAGES

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]

    def changefreq(self, item):
        return item[2]


class ServiceSitemap(Sitemap):
    protocol = "https"
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return Service.objects.published().exclude(body="")


class SolutionGroupSitemap(Sitemap):
    protocol = "https"
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return [code for code in Solution.Group.values if Solution.objects.published().filter(group=code).exists()]

    def location(self, item):
        return reverse("web:solutions_group", kwargs={"group": item})


class SolutionSitemap(Sitemap):
    protocol = "https"
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return Solution.objects.published()


class ArticleSitemap(Sitemap):
    protocol = "https"
    priority = 0.6
    changefreq = "yearly"

    def items(self):
        return Article.objects.published()

    def lastmod(self, item):
        return item.published_at


SITEMAPS = {
    "pages": StaticSitemap,
    "services": ServiceSitemap,
    "solution_groups": SolutionGroupSitemap,
    "solutions": SolutionSitemap,
    "articles": ArticleSitemap,
}
