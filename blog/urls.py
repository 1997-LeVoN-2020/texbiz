from django.urls import path

from . import views
from .feeds import ArticleFeed

app_name = "blog"

urlpatterns = [
    path("", views.index, name="index"),
    path("feed/", ArticleFeed(), name="feed"),
    path("<slug:slug>/", views.article, name="article"),
]
