"""Статьи блога. Текст хранится готовым HTML, загружается из blog/fixtures/."""
from django.db import models
from django.urls import reverse
from django.utils import timezone


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Article(models.Model):
    title = models.CharField("Заголовок", max_length=250)
    slug = models.SlugField("Адрес", unique=True, max_length=120)
    excerpt = models.CharField("Анонс", max_length=300)
    body = models.TextField("Текст (HTML)")
    published_at = models.DateTimeField("Дата публикации", help_text="Дата в будущем — отложенная публикация")
    meta_title = models.CharField("Title для поиска", max_length=200, blank=True)
    meta_description = models.CharField("Description для поиска", max_length=300, blank=True)
    is_published = models.BooleanField("Опубликовано", default=False)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "статья"
        verbose_name_plural = "статьи"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:article", kwargs={"slug": self.slug})

    @property
    def page_title(self):
        return self.meta_title or f"{self.title} | Блог ТЕХБИЗ"
