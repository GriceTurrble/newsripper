from django.urls import path

from . import views

app_name = "ripper"

urlpatterns = [
    # Index, using the Article list
    path("", views.ArticleListView.as_view(), name="index"),
    # Article paths
    # NOTE: The order of these paths is important!
    # - PK comes first, so a matching path is caught in the redirect
    path(
        "article/<int:pk>",
        views.ArticleRedirectView.as_view(),
        name="article_pk_redirect",
    ),
    # - Special paths must come BEFORE the DetailView
    #   (otherwise they would be captured as the `path:url` arg and never work).
    path("article/delete/", views.delete_article, name="delete_article"),
    path("article/process-new/", views.process_article, name="process_article"),
    path("article/reprocess/", views.reprocess_article, name="reprocess_article"),
    # - DetailView always comes last, as a catch-all for all URL paths.
    path(
        "article/<path:url>", views.ArticleDetailView.as_view(), name="article_detail"
    ),
]
