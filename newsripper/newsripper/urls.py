from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("ripper.urls", namespace="ripper")),
    path("admin/", admin.site.urls),
]
