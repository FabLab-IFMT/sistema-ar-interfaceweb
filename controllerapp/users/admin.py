from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, Card, ProjectistRequest, RegistrationRequest, SolicitacaoLGPD


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'roles')
    search_fields = ('id', 'first_name', 'last_name', 'email')
    ordering = ('first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('id', 'password')}),
        ('Informações pessoais', {'fields': ('first_name', 'last_name', 'email', 'profile_image')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'roles', 'email_verified')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id', 'first_name', 'last_name', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_staff_equivalent')
    search_fields = ('code', 'name')


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'user')
    search_fields = ('card_number', 'user__first_name', 'user__last_name', 'user__id')


@admin.register(ProjectistRequest)
class ProjectistRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'decided_by')
    list_filter = ('status',)
    search_fields = ('user__first_name', 'user__last_name', 'user__id')


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'id_number', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('first_name', 'last_name', 'email', 'id_number')


@admin.register(SolicitacaoLGPD)
class SolicitacaoLGPDAdmin(admin.ModelAdmin):
    list_display = ('email_snapshot', 'tipo', 'status', 'solicitado_em', 'concluido_em')
    list_filter = ('tipo', 'status')
    search_fields = ('email_snapshot',)
    readonly_fields = ('email_snapshot', 'tipo', 'solicitado_em', 'concluido_em', 'usuario')
    ordering = ('-solicitado_em',)

    def has_add_permission(self, request):
        return False  # Solicitações só são criadas pelo sistema
