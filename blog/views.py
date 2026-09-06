from django.conf import settings
from django.shortcuts import get_object_or_404, render

from web.seo import jsonld, page_meta
from web.views import lead_form

from .models import Article


def index(request):
    return render(
        request,
        "blog/index.html",
        {
            "page": page_meta(
                request,
                title="Блог об автоматизации отелей | ТЕХБИЗ",
                description="Статьи об автоматизации гостиничного бизнеса: внедрение 1С, выбор онлайн-касс, серверная инфраструктура и замковые системы для отелей.",
            ),
            "articles": Article.objects.published(),
        },
    )


def article(request, slug):
    article = get_object_or_404(Article.objects.published(), slug=slug)
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": article.meta_description or article.excerpt,
        "author": {"@type": "Organization", "name": settings.SITE_NAME},
        "publisher": {"@type": "Organization", "name": settings.SITE_NAME},
        "datePublished": article.published_at.date().isoformat(),
        "image": settings.SITE_URL + "/static/img/og-cover.png",
        "mainEntityOfPage": settings.SITE_URL + request.path,
    }
    return render(
        request,
        "blog/article.html",
        {
            "page": page_meta(
                request,
                title=article.page_title,
                description=article.meta_description or article.excerpt,
                og_type="article",
                og_title=article.title,
            ),
            "article": article,
            "more": Article.objects.published().exclude(pk=article.pk)[:3],
            "form": lead_form(request),
            "jsonld": [jsonld(schema)],
        },
    )
