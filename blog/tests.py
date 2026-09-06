"""Тесты блога: что опубликовано, то видно; черновики и будущие даты — нет."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article


class ArticleVisibilityTests(TestCase):
    fixtures = ["articles.json"]

    def test_published_article_opens(self):
        article = Article.objects.published().first()
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 200)

    def test_draft_is_not_reachable(self):
        article = Article.objects.published().first()
        article.is_published = False
        article.save()
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 404)

    def test_future_date_postpones_publication(self):
        article = Article.objects.published().first()
        article.published_at = timezone.now() + timedelta(days=7)
        article.save()
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 404)
        self.assertNotIn(article, Article.objects.published())

    def test_index_lists_only_published(self):
        hidden = Article.objects.published().first()
        hidden.is_published = False
        hidden.save()
        response = self.client.get(reverse("blog:index"))
        self.assertNotContains(response, hidden.get_absolute_url())

    def test_all_twelve_articles_carried_over_from_the_old_site(self):
        self.assertEqual(Article.objects.published().count(), 12)

    def test_article_addresses_match_the_old_site(self):
        """Адреса статей проиндексированы — менять их нельзя."""
        for slug in [
            "1c-avtomatizaciya-otelya-s-chego-nachat",
            "kak-vybrat-onlayn-kassu-dlya-gostinicy",
            "chek-list-podgotovki-otelya-k-vysokomu-sezonu",
        ]:
            with self.subTest(slug=slug):
                self.assertEqual(self.client.get(f"/blog/{slug}/").status_code, 200)


class ArticleMarkupTests(TestCase):
    fixtures = ["articles.json"]

    def test_article_carries_json_ld(self):
        article = Article.objects.published().first()
        self.assertContains(self.client.get(article.get_absolute_url()), "application/ld+json")

    def test_body_html_is_rendered_not_escaped(self):
        article = Article.objects.published().first()
        self.assertContains(self.client.get(article.get_absolute_url()), "<h2>")
