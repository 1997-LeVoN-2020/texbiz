"""
Тесты сайта. Главное здесь — путь заявки: на прежней версии сайта обработчик
формы не был развёрнут, и обращения пропадали. Всё, что защищает заявку от
потери, покрыто отдельными тестами.

Запуск:  .venv/Scripts/python manage.py test
"""
import time
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import LeadForm
from .models import Lead, Service, Solution


def lead_data(**overrides):
    """Заполненная форма. ts со сдвигом назад: иначе сработает защита от ботов."""
    data = {
        "name": "Иван Петров",
        "phone": "+7 938 511-13-31",
        "object_type": "Отель",
        "consent": "1",
        "ts": str(int(time.time()) - 30),
        "source_page": "/kontakty/",
    }
    data.update(overrides)
    return data


class LeadFormTests(TestCase):
    """Проверка полей до сохранения."""

    def test_phone_normalized_to_one_shape(self):
        variants = [
            "+7 938 511-13-31",
            "8 938 511 13 31",
            "89385111331",
            "9385111331",
            "+7 (938) 511-13-31",
        ]
        for raw in variants:
            with self.subTest(raw=raw):
                form = LeadForm(data=lead_data(phone=raw))
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["phone"], "+79385111331")

    def test_short_phone_rejected(self):
        form = LeadForm(data=lead_data(phone="12345"))
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_name_must_not_be_a_single_character(self):
        form = LeadForm(data=lead_data(name="И"))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_name_whitespace_collapsed(self):
        form = LeadForm(data=lead_data(name="  Иван   Петров  "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["name"], "Иван Петров")

    def test_consent_is_required_by_152fz(self):
        data = lead_data()
        data.pop("consent")
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("consent", form.errors)

    def test_optional_fields_may_be_empty(self):
        form = LeadForm(data=lead_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "")
        self.assertIsNone(form.cleaned_data["rooms_count"])

    def test_long_message_truncated(self):
        form = LeadForm(data=lead_data(message="я" * 5000))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data["message"]), 4000)


class LeadSubmitTests(TestCase):
    """Приём заявки целиком: сохранение, уведомление, ответ."""

    def setUp(self):
        cache.clear()  # лимит по IP живёт в кэше и протёк бы между тестами
        self.url = reverse("web:lead_submit")
        self.thanks = reverse("web:thanks")

    def post(self, data=None, ajax=False):
        headers = {"HTTP_X_REQUESTED_WITH": "fetch", "HTTP_ACCEPT": "application/json"} if ajax else {}
        return self.client.post(self.url, data if data is not None else lead_data(), **headers)

    # --- Обычная отправка, без JavaScript ---

    def test_without_javascript_saves_and_redirects(self):
        response = self.post()
        self.assertRedirects(response, self.thanks)
        lead = Lead.objects.get()
        self.assertEqual(lead.name, "Иван Петров")
        self.assertEqual(lead.phone, "+79385111331")
        self.assertEqual(lead.status, Lead.Status.NEW)
        self.assertEqual(lead.source_page, "/kontakty/")

    def test_invalid_without_javascript_returns_page_with_errors(self):
        response = self.post(lead_data(phone="123"))
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "field-error", status_code=422)
        self.assertEqual(Lead.objects.count(), 0)

    # --- Отправка с JavaScript ---

    def test_with_javascript_returns_json_and_redirect_target(self):
        response = self.post(ajax=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "redirect": self.thanks})
        self.assertEqual(Lead.objects.count(), 1)

    def test_with_javascript_returns_field_errors(self):
        response = self.post(lead_data(name="", phone="1"), ajax=True)
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertIn("name", body["errors"])
        self.assertIn("phone", body["errors"])
        self.assertEqual(Lead.objects.count(), 0)

    # --- Антиспам ---

    def test_honeypot_looks_successful_but_saves_nothing(self):
        response = self.post(lead_data(website="https://spam.example"))
        self.assertRedirects(response, self.thanks)
        self.assertEqual(Lead.objects.count(), 0)

    def test_form_submitted_too_fast_is_dropped(self):
        response = self.post(lead_data(ts=str(int(time.time()))))
        self.assertRedirects(response, self.thanks)
        self.assertEqual(Lead.objects.count(), 0)

    def test_missing_timestamp_does_not_punish_a_person(self):
        """Без JavaScript поле ts может не заполниться — заявка всё равно принимается."""
        data = lead_data()
        data.pop("ts")
        self.post(data)
        self.assertEqual(Lead.objects.count(), 1)

    def test_rate_limit_stops_flooding(self):
        for _ in range(5):
            self.post()
        self.assertEqual(Lead.objects.count(), 5)
        response = self.post(ajax=True)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Lead.objects.count(), 5)

    # --- Надёжность: заявка не должна теряться ---

    def test_lead_survives_mail_failure(self):
        """Сбой SMTP не отменяет заявку и не показывает клиенту ошибку."""
        with patch("web.views.send_mail", side_effect=OSError("SMTP недоступен")):
            response = self.post()
        self.assertRedirects(response, self.thanks)
        self.assertEqual(Lead.objects.count(), 1)

    def test_notification_contains_every_field(self):
        self.post(lead_data(email="a@b.ru", rooms_count="40", message="нужны кассы"))
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        for expected in ["Иван Петров", "+79385111331", "a@b.ru", "40", "нужны кассы"]:
            self.assertIn(expected, body)

    def test_email_headers_cannot_be_manipulated(self):
        """Ни переносом строки, ни текстом из формы: в теме только номер заявки."""
        self.post(lead_data(name="Иван\r\nBcc: chужой@example.com"))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, f"Новая заявка с сайта ТЕХБИЗ №{Lead.objects.get().pk}")
        self.assertEqual(message.recipients(), ["info@tex-biz.ru"])
        # Перенос строки схлопнут ещё в форме, до письма он не доходит.
        self.assertNotIn("\n", Lead.objects.get().name)

    # --- Метод ---

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class PageTests(TestCase):
    """Страницы открываются, служебные закрыты от индексации."""

    fixtures = ["services.json", "solutions.json", "articles.json"]

    def test_public_pages_open(self):
        for name in ["web:home", "web:services", "web:solutions", "web:booking", "web:contacts", "blog:index"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_service_pages_keep_their_old_addresses(self):
        """Адреса проиндексированы поисковиками — пропасть не должны."""
        for slug in [
            "1c-avtomatizaciya-otelya",
            "onlain-kassy-dlya-gostinicy",
            "nastroika-serverov-otelya",
            "integraciya-zamkovyh-sistem",
        ]:
            with self.subTest(slug=slug):
                self.assertEqual(self.client.get(f"/{slug}/").status_code, 200)

    def test_service_without_a_page_is_not_reachable(self):
        service = Service.objects.filter(body="").first()
        self.assertIsNotNone(service)
        self.assertEqual(self.client.get(f"/{service.slug}/").status_code, 404)

    def test_unpublished_service_is_hidden(self):
        service = Service.objects.exclude(body="").first()
        service.is_published = False
        service.save()
        self.assertEqual(self.client.get(f"/{service.slug}/").status_code, 404)

    def test_unknown_address_returns_404(self):
        self.assertEqual(self.client.get("/takoy-stranicy-net/").status_code, 404)

    def test_service_and_solution_counts_match_the_fixtures(self):
        self.assertEqual(Service.objects.count(), 8)
        self.assertEqual(Solution.objects.count(), 4)


class SeoTests(TestCase):
    fixtures = ["services.json", "solutions.json", "articles.json"]

    def test_private_pages_are_noindex(self):
        for name in ["web:privacy", "web:thanks"]:
            with self.subTest(page=name):
                self.assertContains(self.client.get(reverse(name)), "noindex")

    def test_public_pages_are_indexable(self):
        self.assertNotContains(self.client.get(reverse("web:home")), "noindex")

    def test_sitemap_lists_services_and_hides_private_pages(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/1c-avtomatizaciya-otelya/", body)
        self.assertNotIn("/privacy/", body)
        self.assertNotIn("/spasibo/", body)

    def test_robots_points_at_the_sitemap(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Sitemap:", body)
        self.assertIn("Disallow: /send/", body)

    def test_every_page_declares_a_canonical(self):
        for url in ["/", "/uslugi/", "/booking/", "/1c-avtomatizaciya-otelya/"]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'rel="canonical"')

    @override_settings(DEBUG=False)
    def test_metrika_counter_present_outside_debug(self):
        self.assertContains(self.client.get(reverse("web:home")), "110630521")

    def test_metrika_counter_absent_in_debug(self):
        with override_settings(DEBUG=True):
            self.assertNotContains(self.client.get(reverse("web:home")), "mc.yandex.ru")
