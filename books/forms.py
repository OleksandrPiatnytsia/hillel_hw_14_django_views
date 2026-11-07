from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator

from .models import Author, Book, BookQuerySet, Category

COVER_MAX_SIZE_MB = 2
COVER_ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


class CoverInput(forms.ClearableFileInput):
    """File input with a preview of the current cover and a "Remove" checkbox.

    Same logic as Django's ClearableFileInput, only the HTML is replaced
    with Bootstrap markup (see the template).
    """

    template_name = "books/widgets/cover_input.html"


class BookForm(forms.ModelForm):
    """Create / update a book, styled with Bootstrap classes."""

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "price",
            "stock",
            "categories",
            "description",
            "cover",
        ]
        help_texts = {
            "author": "New authors are added in the admin.",
            "cover": (
                f"JPG, PNG or WebP, up to {COVER_MAX_SIZE_MB} MB. "
                "Without a cover a placeholder is shown."
            ),
        }
        widgets = {
            # accept: the browser's file dialog shows only these types
            # (just a convenience — the real check is in clean_cover)
            "cover": CoverInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            # ForeignKey -> <select> with all authors (ModelChoiceField)
            "author": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            # Through model (BookCategory) has no extra required fields,
            # so ModelForm.save() can write the M2M as usual
            "categories": forms.CheckboxSelectMultiple(
                attrs={"class": "form-check-input"}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_cover(self):
        """Extra checks on top of ImageField (which already verifies via Pillow
        that the file is a real image)."""
        cover = self.cleaned_data.get("cover")
        # Only a newly uploaded file needs checking. Otherwise the value is
        # the current cover (nothing uploaded) or False ("Remove" checked).
        if isinstance(cover, UploadedFile):
            FileExtensionValidator(COVER_ALLOWED_EXTENSIONS)(cover)
            if cover.size > COVER_MAX_SIZE_MB * 1024 * 1024:
                size_mb = cover.size / (1024 * 1024)
                raise forms.ValidationError(
                    f"The file is {size_mb:.1f} MB, the limit is {COVER_MAX_SIZE_MB} MB."
                )
        return cover


class BookFilterForm(forms.Form):
    """GET filters for the book catalog. All fields are optional."""

    SORT_CHOICES = [
        ("title", "Title A→Z"),
        ("-title", "Title Z→A"),
        ("author__name", "Author A→Z"),
        ("price", "Price: low to high"),
        ("-price", "Price: high to low"),
        ("-created_at", "Newest first"),
    ]

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Title or author"}
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        to_field_name="slug",  # ?category=fantasy instead of ?category=3
        empty_label="All categories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    author = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        required=False,  # ?author=<pk>
        empty_label="All authors",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    stock = forms.ChoiceField(
        choices=[("", "Any")] + BookQuerySet.STOCK_STATUS_CHOICES,
        required=False,
        label="Availability",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    price_min = forms.DecimalField(
        required=False,
        min_value=0,
        label="Price from",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    price_max = forms.DecimalField(
        required=False,
        min_value=0,
        label="Price to",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        label="Sort by",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get("price_min")
        price_max = cleaned_data.get("price_max")
        if price_min is not None and price_max is not None and price_min > price_max:
            raise forms.ValidationError("“Price from” can't be greater than “Price to”.")
        return cleaned_data
