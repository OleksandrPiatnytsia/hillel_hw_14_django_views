"""Unicode-aware case-insensitive LIKE for SQLite.

Problem: SQLite's built-in LIKE ignores case only for ASCII letters, so
`Book.objects.filter(title__icontains="вбив")` doesn't find "Вбивство".
Django translates contains / icontains / startswith / endswith (and their
"i" versions) on SQLite into `LIKE %s ESCAPE '\\'`.

Fix: SQLite lets us replace the function behind the LIKE operator with our
own Python function (sqlite3 `create_function("like", ...)`). We register it
for every new SQLite connection. Then catalog search, admin search and
`book_stats --search` all become case-insensitive for Cyrillic too.

Trade-offs (fine for a small educational project):
- LIKE runs in Python, a bit slower than the native one;
- SQLite can't use an index for LIKE anymore (it couldn't for %...% anyway);
- like the native SQLite LIKE, `contains` (without "i") is also case-insensitive.

On PostgreSQL / MySQL this module does nothing: they handle Unicode case themselves.
"""

import re
from functools import lru_cache


@lru_cache(maxsize=256)
def _like_pattern_to_regex(pattern, escape):
    """Translate an SQL LIKE pattern into a compiled regular expression.

    %  -> any sequence of characters (.*)
    _  -> exactly one character (.)
    escape + char -> that char literally (Django escapes user's % and _ this way)
    """
    parts = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if escape and char == escape and i + 1 < len(pattern):
            parts.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        if char == "%":
            parts.append(".*")
        elif char == "_":
            parts.append(".")
        else:
            parts.append(re.escape(char))
        i += 1
    return re.compile("".join(parts), re.DOTALL)


def unicode_like(pattern, value, escape=None):
    """Replacement for SQLite's like(X, Y[, Z]) — note: pattern comes first.

    casefold() is a "stronger" lower(): it's meant exactly for
    case-insensitive comparison of any language.
    """
    if pattern is None or value is None:
        return None  # SQL: comparing with NULL gives NULL
    regex = _like_pattern_to_regex(pattern.casefold(), escape)
    return regex.fullmatch(str(value).casefold()) is not None


def register_unicode_like(sender, connection, **kwargs):
    """Handler for django.db.backends.signals.connection_created."""
    if connection.vendor != "sqlite":
        return
    # connection.connection — the raw sqlite3.Connection under Django's wrapper.
    # LIKE without ESCAPE calls like(X, Y), with ESCAPE — like(X, Y, Z).
    raw = connection.connection
    raw.create_function("like", 2, unicode_like, deterministic=True)
    raw.create_function("like", 3, unicode_like, deterministic=True)
