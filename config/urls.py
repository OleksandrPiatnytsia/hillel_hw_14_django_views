from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Bookstore catalog lives at the site root; namespace "books" comes
    # from app_name in books/urls.py
    path("", include("books.urls")),
]

if settings.DEBUG:
    # Uploaded files (covers) in development. runserver serves static files
    # by itself, but not media. In production nginx / storage does this.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
