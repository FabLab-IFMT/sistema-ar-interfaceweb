from django.contrib import admin

from .models import InsightIA


@admin.register(InsightIA)
class InsightIAAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'foco', 'modelo_usado', 'tokens_usados', 'gerado_por', 'criado_em')
    list_filter = ('foco', 'criado_em')
    search_fields = ('titulo', 'conteudo')
    readonly_fields = ('criado_em',)
