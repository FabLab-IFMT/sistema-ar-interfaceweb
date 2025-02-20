from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, Card

class CardInline(admin.StackedInline):  # Permite editar cartões diretamente no usuário
    model = Card
    extra = 0  # Não adiciona linhas vazias automaticamente
    fields = ("card_number",)
    verbose_name_plural = "Cartão de Ponto"

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("id", "first_name", "last_name", "email", "is_staff", "is_active", "has_card")
    list_filter = ("is_staff", "is_active")

    fieldsets = (
        (_("Dados"), {"fields": ("id", "password")}),
        (_("Informações Pessoais"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissões"),
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
        (_("Datas Importantes"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "id", "email", "first_name", "last_name", "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
        ),
    )

    search_fields = ("id", "first_name", "last_name", "email")
    ordering = ("id",)
    inlines = [CardInline]  # Permite editar cartões dentro da edição de usuário

    def has_card(self, obj):
        return hasattr(obj, "card")
    has_card.boolean = True
    has_card.short_description = "Possui Cartão"

# Registra o usuário e permite edição do cartão junto
admin.site.register(CustomUser, CustomUserAdmin)

# Caso prefira gerenciar cartões separadamente, mantenha esta linha:
admin.site.register(Card)
