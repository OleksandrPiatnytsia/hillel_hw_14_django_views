from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Bookstore catalog lives at the site root; namespace "books" comes
    # from app_name in books/urls.py
    path("", include("books.urls")),
]
