"""
Модели раздела «сайт»: услуги, решения по формату объекта, заявки.

Все модели плоские, без связанных таблиц. Содержимое услуг и решений
загружается из фикстур (web/fixtures/), заявки создаёт форма на сайте.
"""
from django.db import models
from django.urls import reverse

from .icons import ICON_CHOICES


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class Service(models.Model):
    """Услуга. Если body пуст, у услуги нет своей страницы — только карточка в списке."""

    title = models.CharField("Название", max_length=200)
    slug = models.SlugField("Адрес", unique=True, help_text="Страница открывается по /<slug>/")
    icon = models.CharField("Значок", max_length=16, choices=ICON_CHOICES, default="OPS")
    summary = models.CharField("Текст карточки", max_length=300)
    lead = models.TextField("Лид-абзац страницы", blank=True)
    body = models.TextField("Содержимое страницы (HTML)", blank=True)
    meta_title = models.CharField("Title для поиска", max_length=200, blank=True)
    meta_description = models.CharField("Description для поиска", max_length=300, blank=True)
    order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_published = models.BooleanField("Опубликовано", default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "услуга"
        verbose_name_plural = "услуги"

    def __str__(self):
        return self.title

    @property
    def has_page(self):
        return bool(self.body)

    def get_absolute_url(self):
        return reverse("web:service", kwargs={"slug": self.slug})

    @property
    def page_title(self):
        return self.meta_title or f"{self.title} | ТЕХБИЗ"


class Solution(models.Model):
    """Решение под формат объекта: отель, мини-отель, апартаменты, сеть."""

    title = models.CharField("Название", max_length=200)
    slug = models.SlugField("Якорь", unique=True, help_text="Блок на странице /resheniya/#<slug>")
    body = models.TextField("Текст (HTML)")
    order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_published = models.BooleanField("Опубликовано", default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "решение"
        verbose_name_plural = "решения"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("web:solutions") + f"#{self.slug}"


class Lead(models.Model):
    """Заявка с формы. Поля клиента после сохранения не меняются; для работы — status."""

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_WORK = "work", "В работе"
        CLOSED = "closed", "Закрыта"
        SPAM = "spam", "Спам"

    name = models.CharField("Имя", max_length=150)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("E-mail", blank=True)
    object_type = models.CharField("Тип объекта", max_length=60)
    rooms_count = models.PositiveIntegerField("Номерной фонд", null=True, blank=True)
    message = models.TextField("Задача", blank=True)
    source_page = models.CharField("Страница отправки", max_length=255, blank=True)
    consent = models.BooleanField("Согласие на обработку данных", default=False)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "заявка"
        verbose_name_plural = "заявки"

    def __str__(self):
        return f"{self.name}, {self.phone}"
