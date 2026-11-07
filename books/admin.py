from django.contrib import admin
from django.db.models import Count

from .models import Book, BookCategory, BookQuerySet, Category


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------


class BaseBookCategoryInline(admin.TabularInline):
    model = BookCategory

    def get_queryset(self, request):
        # Row titles use BookCategory.__str__ (book + category names):
        # join them in one query instead of 2 extra queries per row
        return super().get_queryset(request).select_related("book", "category")


class BookCategoryInline(BaseBookCategoryInline):
    """Categories of a book, shown on the Book page."""

    extra = 1
    autocomplete_fields = ["category"]
    verbose_name = "category"
    verbose_name_plural = "categories"


class CategoryBookInline(BaseBookCategoryInline):
    """Books of a category, shown on the Category page."""

    extra = 0
    autocomplete_fields = ["book"]
    verbose_name = "book"
    verbose_name_plural = "books"


# ---------------------------------------------------------------------------
# Custom filters
# ---------------------------------------------------------------------------


class StockStatusFilter(admin.SimpleListFilter):
    title = "stock status"
    parameter_name = "stock_status"

    def lookups(self, request, model_admin):
        return BookQuerySet.STOCK_STATUS_CHOICES

    def queryset(self, request, queryset):
        return queryset.by_stock_status(self.value())


# ---------------------------------------------------------------------------
# Model admins
# ---------------------------------------------------------------------------


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "books_count"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    # Explicit ordering: Meta.ordering is ignored for annotated (GROUP BY) queries
    ordering = ["name"]
    inlines = [CategoryBookInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(books_count=Count("books"))

    @admin.display(description="books", ordering="books_count")
    def books_count(self, obj):
        return obj.books_count


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "price",
        "stock",
        "is_available",
        "category_list",
        "created_at",
    ]
    list_display_links = ["title"]
    list_editable = ["price", "stock"]
    list_filter = [StockStatusFilter, "categories", "created_at"]
    search_fields = ["title", "author", "description", "categories__name"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]
    inlines = [BookCategoryInline]
    fieldsets = [
        (None, {"fields": ["title", "author", "description"]}),
        ("Sales", {"fields": ["price", "stock"]}),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    def get_queryset(self, request):
        # Load all categories in one extra query instead of one per row
        return super().get_queryset(request).prefetch_related("categories")

    @admin.display(description="categories")
    def category_list(self, obj):
        return ", ".join(category.name for category in obj.categories.all())

    @admin.display(description="available", boolean=True, ordering="stock")
    def is_available(self, obj):
        return obj.stock > 0
