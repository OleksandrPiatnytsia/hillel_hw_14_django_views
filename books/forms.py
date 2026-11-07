from django import forms

from .models import Book, BookQuerySet, Category


class BookForm(forms.ModelForm):
    """Create / update a book, styled with Bootstrap classes."""

    class Meta:
        model = Book
        fields = ["title", "author", "price", "stock", "categories", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
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


class BookFilterForm(forms.Form):
    """GET filters for the book catalog. All fields are optional."""

    SORT_CHOICES = [
        ("title", "Title A→Z"),
        ("-title", "Title Z→A"),
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
