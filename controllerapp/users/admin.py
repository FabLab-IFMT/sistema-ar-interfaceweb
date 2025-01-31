# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("id", "is_staff", "is_active",)
    list_filter = ("id", "is_staff", "is_active",)
    fieldsets = (
        (_("Dados"), {"fields": ("id", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "id",  "email", "first_name", "last_name","password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
        ),
    )

    search_fields = ("id",)
    ordering = ("id",)


admin.site.register(CustomUser, CustomUserAdmin)