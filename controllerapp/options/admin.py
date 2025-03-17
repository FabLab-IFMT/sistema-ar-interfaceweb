from django.contrib import admin
from .models import Material, Membro

# Register your models here.
admin.site.register(Material)

@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'ativo', 'ordem')
    list_filter = ('ativo', 'cargo')
    search_fields = ('nome', 'email', 'bio')
    ordering = ('ordem', 'nome')
    list_editable = ('ordem', 'ativo')
