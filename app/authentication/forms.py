from django import forms

from app.authentication.models import User


class UserProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)
    birthday = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "gender", "birthday"]
