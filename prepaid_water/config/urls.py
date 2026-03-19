"""URL configuration for project routes and API endpoints."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("billing.urls")),
]
