from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm

from app.authentication.models import User

# Register your models here.
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "user_role",
    )
    change_form_template = "loginas/custom_change_form.html"
    add_form = UserCreationForm

    # Ensure that when creating or updating users, passwords are hashed
    def save_model(self, request, obj, form, change):
        if form.cleaned_data["password"]:
            obj.set_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)
