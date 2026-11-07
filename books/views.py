from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import BookFilterForm, BookForm
from .models import Book


class BookListView(ListView):
    """Catalog: filters from GET parameters + pagination.

    Template: books/book_list.html (default name: <app>/<model>_list.html)
    """

    model = Book
    context_object_name = "books"
    paginate_by = 10

    def get_queryset(self):
        # Categories of all books on the page in one extra query, not one per book
        queryset = super().get_queryset().prefetch_related("categories")

        # Unbound form (None) when there are no GET params -> no validation errors
        self.filter_form = BookFilterForm(self.request.GET or None)
        if not self.filter_form.is_valid():
            return queryset

        data = self.filter_form.cleaned_data
        if data["q"]:
            queryset = queryset.filter(
                Q(title__icontains=data["q"]) | Q(author__icontains=data["q"])
            )
        if data["category"]:
            queryset = queryset.filter(categories=data["category"])
        queryset = queryset.by_stock_status(data["stock"])
        if data["price_min"] is not None:
            queryset = queryset.filter(price__gte=data["price_min"])
        if data["price_max"] is not None:
            queryset = queryset.filter(price__lte=data["price_max"])
        if data["sort"]:
            # "pk" as a tie-breaker: books with equal price keep a stable order,
            # so the same book doesn't jump between pages
            queryset = queryset.order_by(data["sort"], "pk")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class BookDetailView(DetailView):
    """Single book. Template: books/book_detail.html"""

    model = Book
    context_object_name = "book"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("categories")


class BookCreateView(SuccessMessageMixin, CreateView):
    """New book. Template: books/book_form.html (shared with update).

    No success_url: after saving, Django redirects to book.get_absolute_url().
    """

    model = Book
    form_class = BookForm
    success_message = "Book “%(title)s” was created."


class BookUpdateView(SuccessMessageMixin, UpdateView):
    """Edit a book. Template: books/book_form.html (shared with create)."""

    model = Book
    form_class = BookForm
    success_message = "Book “%(title)s” was updated."


class BookDeleteView(SuccessMessageMixin, DeleteView):
    """GET -> confirmation page, POST -> delete.

    Template: books/book_confirm_delete.html
    """

    model = Book
    context_object_name = "book"
    success_url = reverse_lazy("books:list")

    def get_success_message(self, cleaned_data):
        # Delete form has no fields, so take the title from the deleted object
        return f"Book “{self.object.title}” was deleted."
