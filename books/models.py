from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.templatetags.static import static
from django.urls import reverse

LOW_STOCK_THRESHOLD = 5


class BookQuerySet(models.QuerySet):
    STOCK_IN = "in_stock"
    STOCK_LOW = "low"
    STOCK_OUT = "out"
    STOCK_STATUS_CHOICES = [
        (STOCK_IN, "In stock"),
        (STOCK_LOW, f"Low (≤ {LOW_STOCK_THRESHOLD})"),
        (STOCK_OUT, "Out of stock"),
    ]

    def by_stock_status(self, status):
        """Filter by one of STOCK_STATUS_CHOICES; unknown/empty value -> no filter."""
        if status == self.STOCK_IN:
            return self.filter(stock__gt=0)
        if status == self.STOCK_LOW:
            return self.filter(stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD)
        if status == self.STOCK_OUT:
            return self.filter(stock=0)
        return self


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    # Only the path is stored in the DB; the file goes to MEDIA_ROOT/covers/<year>/<month>/
    cover = models.ImageField(upload_to="covers/%Y/%m/", blank=True)
    categories = models.ManyToManyField(
        Category,
        through="BookCategory",
        related_name="books",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BookQuerySet.as_manager()

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} — {self.author_name}"

    def get_absolute_url(self):
        return reverse("books:detail", kwargs={"pk": self.pk})

    @property
    def cover_url(self):
        """Uploaded cover or the static placeholder — templates don't need if/else."""
        if self.cover:
            return self.cover.url
        return static("img/no-cover.svg")

    @property
    def is_low_stock(self):
        return 0 < self.stock <= LOW_STOCK_THRESHOLD


class BookCategory(models.Model):
    """Link between Book and Category.

    An explicit through model lets us protect categories from deletion
    while they still contain books (plain M2M has no on_delete).
    """

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "book category"
        verbose_name_plural = "book categories"
        constraints = [
            models.UniqueConstraint(
                fields=["book", "category"],
                name="unique_book_category",
            ),
        ]

    def __str__(self):
        return f"{self.book.title} → {self.category.name}"
