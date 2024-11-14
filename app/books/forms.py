from django import forms
from tinymce.widgets import TinyMCE

from app.books.models import Books, Categories, BooksChapter


class CustomBooleanSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        # Override the choices to remove the "Unknown" option
        choices = [
            (True, "Yes"),
            (False, "No"),
        ]
        kwargs["choices"] = choices
        super().__init__(*args, **kwargs)


class BookForm(forms.ModelForm):
    class Meta:
        model = Books
        fields = ["title", "description", "cover_photo", "category"]
        labels = {
            # "is_published": "Ready to published?",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "block w-full px-3 py-2 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:outline-blue-600",
                }
            ),  # Tailwind styling added
            "cover_photo": forms.ClearableFileInput(
                attrs={
                    "class": "block w-full py-1.5 px-2 text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-blue-600"
                }
            ),
            "category": forms.CheckboxSelectMultiple(
                attrs={
                    "class": "max-h-60 overflow-auto border border-gray-300 rounded-lg bg-gray-50 p-2"
                }
            ),
            # "is_published": CustomBooleanSelect(),
        }

    category = forms.ModelMultipleChoiceField(
        queryset=Categories.objects.all(),
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "max-h-60 overflow-auto border border-gray-300 rounded-lg bg-gray-50 p-2"
            }
        ),
    )


class BookContentForm(forms.ModelForm):
    class Meta:
        model = BooksChapter
        fields = ["title", "is_draft", "is_locked"]
        labels = {
            "is_draft": "Is draft?",
            "is_locked": "Is this chapter locked?",
        }
        widgets = {
            "is_draft": CustomBooleanSelect(),
            "is_locked": CustomBooleanSelect(),
        }
