"""Страницы раздела «сайт» и приём заявок."""
import logging
import time
import urllib.error
import urllib.request
import json

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from blog.models import Article

from .forms import LeadForm
from .models import Lead, Service, Solution
from .seo import faq_page, jsonld, organization, page_meta

log = logging.getLogger("web.leads")

# Вопросы главной страницы: в FAQ-блок и в микроразметку FAQPage.
HOME_FAQ = [
    (
        "Сколько стоит внедрение 1С и касс для отеля?",
        "Стоимость рассчитывается после аудита объекта. На цену влияет количество рабочих мест, касс, интеграций и сложность инфраструктуры.",
    ),
    (
        "Можно ли внедрять поэтапно без остановки работы отеля?",
        "Да. Мы разбиваем внедрение на этапы и выполняем переключение в низконагруженные периоды.",
    ),
    (
        "Работаете ли вы с уже установленной инфраструктурой?",
        "Да, проводим аудит текущей системы и адаптируем решение под существующее оборудование, если это технически целесообразно.",
    ),
    (
        "Можно ли принимать бронирования и оплату прямо на сайте отеля?",
        "Да, для этого есть отдельный модуль онлайн-бронирования: гость выбирает номер и оплачивает его на сайте отеля, бронь сразу уходит в 1С-Отель без комиссии агрегаторов.",
    ),
]


def lead_form(request):
    """Пустая форма для страницы: время показа и адрес страницы подставляются в скрытые поля."""
    return LeadForm(initial={"ts": int(time.time()), "source_page": request.path})


# --- Страницы --------------------------------------------------------------


def home(request):
    services = Service.objects.published()
    solutions = Solution.objects.published()
    articles = Article.objects.published()[:3]
    return render(
        request,
        "web/home.html",
        {
            "page": page_meta(
                request,
                title="Автоматизация отелей под ключ: 1С, кассы, серверы | ТЕХБИЗ",
                description="ТЕХБИЗ внедряет 1С для отелей, настраивает онлайн-кассы, серверы и замковые системы. Комплексная автоматизация гостиниц под ключ с поддержкой 24/7.",
                og_title="Автоматизация отелей под ключ в 1С | ТЕХБИЗ",
                og_description="Внедрение 1С для отелей, онлайн-кассы, серверная инфраструктура и замковые системы. Пусконаладка и сопровождение.",
            ),
            "services": services,
            "solutions": solutions,
            "articles": articles,
            "faq": HOME_FAQ,
            "form": lead_form(request),
            "jsonld": [jsonld(organization()), jsonld(faq_page(HOME_FAQ))],
        },
    )


def services_index(request):
    return render(
        request,
        "web/services.html",
        {
            "page": page_meta(
                request,
                title="Услуги автоматизации гостиниц: 1С, кассы, серверы, замки | ТЕХБИЗ",
                description="Все услуги ТЕХБИЗ для отелей: внедрение 1С, онлайн-кассы, серверы и сеть, замковые системы, интеграция каналов продаж, миграция без простоя, обучение и поддержка 24/7 с SLA.",
            ),
            "services": Service.objects.published(),
            "form": lead_form(request),
        },
    )


def service_detail(request, slug):
    service = get_object_or_404(Service.objects.published().exclude(body=""), slug=slug)
    schema = {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": service.title,
        "name": service.title,
        "description": service.meta_description or service.summary,
        "provider": {"@type": "Organization", "name": settings.SITE_NAME, "url": settings.SITE_URL + "/"},
        "areaServed": "RU",
    }
    return render(
        request,
        "web/service.html",
        {
            "page": page_meta(
                request,
                title=service.page_title,
                description=service.meta_description or service.summary,
            ),
            "service": service,
            "form": lead_form(request),
            "jsonld": [jsonld(schema)],
        },
    )


def solutions(request):
    return render(
        request,
        "web/solutions.html",
        {
            "page": page_meta(
                request,
                title="Решения по формату объекта для отелей | ТЕХБИЗ",
                description="Автоматизация под формат объекта: городской и курортный отель, мини-отель и гостевой дом, апартаменты и УК, сеть отелей. Подбираем стек под ваш процесс.",
            ),
            "solutions": Solution.objects.published(),
            "form": lead_form(request),
        },
    )


def booking(request):
    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Модуль онлайн-бронирования ТЕХБИЗ",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": "Модуль онлайн-бронирования и оплаты номеров для сайта отеля с интеграцией в 1С-Отель по SOAP, платёжными шлюзами ЮKassa, Сбербанк Эквайринг и PayKeeper.",
        "url": settings.SITE_URL + request.path,
        "provider": {"@type": "Organization", "name": settings.SITE_NAME},
    }
    return render(
        request,
        "web/booking.html",
        {
            "page": page_meta(
                request,
                title="Модуль онлайн-бронирования для сайта отеля | ТЕХБИЗ",
                description="Онлайн-бронирование и оплата номеров прямо на сайте отеля, с интеграцией в 1С-Отель. ЮKassa, Сбербанк Эквайринг, PayKeeper — без комиссии агрегаторов.",
                og_description="Прямые брони и оплата на сайте отеля с интеграцией в 1С-Отель — без комиссии агрегаторов.",
            ),
            "demo_url": settings.BOOKING_DEMO_URL,
            "form": lead_form(request),
            "jsonld": [jsonld(schema)],
        },
    )


def contacts(request, form=None, status=200):
    return render(
        request,
        "web/contacts.html",
        {
            "page": page_meta(
                request,
                title="Контакты ТЕХБИЗ: телефон, почта, реквизиты | ТЕХБИЗ",
                description="Связаться с ТЕХБИЗ: +7 938 511-13-31, info@tex-biz.ru. Работаем по всей России. Реквизиты и форма заявки на аудит объекта.",
            ),
            "form": form or lead_form(request),
        },
        status=status,
    )


def privacy(request):
    return render(
        request,
        "web/privacy.html",
        {
            "page": page_meta(
                request,
                title="Политика обработки персональных данных | ТЕХБИЗ",
                description="Политика обработки персональных данных компании ТЕХБИЗ: какие данные собираются через форму заявки, цели и сроки обработки, права субъекта данных.",
                noindex=True,
            ),
        },
    )


def thanks(request):
    return render(
        request,
        "web/thanks.html",
        {
            "page": page_meta(
                request,
                title="Заявка отправлена | ТЕХБИЗ",
                description="Заявка принята. Мы свяжемся с вами в ближайшее время.",
                noindex=True,
            ),
        },
    )


def not_found(request, exception=None):
    ctx = {
        "page": page_meta(
            request,
            title="Страница не найдена | ТЕХБИЗ",
            description="Запрошенная страница не найдена.",
            noindex=True,
        ),
    }
    return render(request, "web/404.html", ctx, status=404)


def server_error(request):
    ctx = {
        "page": page_meta(
            request,
            title="Ошибка сервера | ТЕХБИЗ",
            description="На сервере произошла ошибка.",
            noindex=True,
        ),
    }
    return render(request, "web/500.html", ctx, status=500)


def robots_txt(request):
    body = f"User-agent: *\nAllow: /\nDisallow: /send/\nDisallow: /spasibo/\n\nSitemap: {settings.SITE_URL}/sitemap.xml\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


# --- Заявка ----------------------------------------------------------------


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _rate_limited(ip):
    key = f"lead-rl:{ip}"
    now = time.time()
    hits = [t for t in cache.get(key, []) if now - t < settings.LEAD_RATE_WINDOW]
    if len(hits) >= settings.LEAD_RATE_LIMIT:
        return True
    hits.append(now)
    cache.set(key, hits, settings.LEAD_RATE_WINDOW)
    return False


def _too_fast(form):
    """Форма отправлена раньше, чем человек успел бы её заполнить."""
    ts = form.data.get("ts")
    try:
        shown = int(ts)
    except (TypeError, ValueError):
        return False  # без JavaScript поле может не заполниться — не наказываем
    return time.time() - shown < settings.LEAD_MIN_FILL_SECONDS


def _lead_text(lead):
    lines = [
        f"Имя: {lead.name}",
        f"Телефон: {lead.phone}",
        f"E-mail: {lead.email or '-'}",
        f"Тип объекта: {lead.object_type}",
        f"Номерной фонд: {lead.rooms_count or '-'}",
        f"Задача: {lead.message or '-'}",
        f"Страница: {settings.SITE_URL}{lead.source_page or '/'}",
        f"Время: {lead.created_at:%d.%m.%Y %H:%M}",
    ]
    return "\n".join(lines)


def _notify(lead):
    """Письмо и Telegram. Любой сбой пишется в лог и не мешает приёму заявки."""
    text = _lead_text(lead)
    try:
        # В теме только номер заявки. Имя приходит из формы, и подставлять его
        # в заголовок письма незачем: оно всё равно есть в теле, а так спамер
        # не напишет что угодно в тему почты владельца. Подмена заголовков
        # невозможна и без этого — clean_name схлопывает переносы строк.
        send_mail(
            subject=f"Новая заявка с сайта ТЕХБИЗ №{lead.pk}",
            message=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.LEAD_NOTIFY_EMAILS,
            fail_silently=False,
        )
    except Exception:
        log.exception("Не удалось отправить письмо о заявке #%s", lead.pk)

    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": settings.TELEGRAM_CHAT_ID, "text": "Новая заявка с сайта ТЕХБИЗ\n\n" + text}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except (urllib.error.URLError, urllib.error.HTTPError):
            log.exception("Не удалось отправить заявку #%s в Telegram", lead.pk)


def _wants_json(request):
    return request.headers.get("X-Requested-With") == "fetch" or "application/json" in request.headers.get("Accept", "")


@require_POST
def lead_submit(request):
    ip = _client_ip(request)
    as_json = _wants_json(request)
    thanks_url = reverse("web:thanks")

    if _rate_limited(ip):
        log.warning("Лимит заявок с IP %s", ip)
        if as_json:
            return JsonResponse({"ok": False, "error": "Слишком много заявок. Позвоните нам по телефону."}, status=429)
        return redirect(thanks_url)

    form = LeadForm(request.POST)

    # Ботам отвечаем как людям, но ничего не сохраняем.
    if form.is_bot or _too_fast(form):
        log.info("Заявка отброшена как спам, IP %s", ip)
        if as_json:
            return JsonResponse({"ok": True, "redirect": thanks_url})
        return redirect(thanks_url)

    if not form.is_valid():
        if as_json:
            errors = {field: errs[0] for field, errs in form.errors.items()}
            return JsonResponse({"ok": False, "errors": errors}, status=422)
        return contacts(request, form=form, status=422)

    lead = form.save(commit=False)
    lead.source_page = (form.cleaned_data.get("source_page") or "")[:255]
    lead.save()
    log.info("Заявка #%s: %s, %s, %s", lead.pk, lead.name, lead.phone, lead.object_type)
    _notify(lead)

    if as_json:
        return JsonResponse({"ok": True, "redirect": thanks_url})
    return redirect(thanks_url)
