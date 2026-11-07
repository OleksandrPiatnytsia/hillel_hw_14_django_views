from django.apps import AppConfig
from django.db.backends.signals import connection_created


class BooksConfig(AppConfig):
    name = "books"

    def ready(self):
        # ready() runs once at startup, after all apps are loaded —
        # the recommended place to connect signals
        from .sqlite_functions import register_unicode_like

        # Every new DB connection gets the Unicode-aware LIKE (SQLite only)
        connection_created.connect(
            register_unicode_like, dispatch_uid="books_unicode_like"
        )
