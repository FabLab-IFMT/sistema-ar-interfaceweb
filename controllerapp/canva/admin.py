from django.contrib import admin
from .models import KanbanColumn, KanbanCard

@admin.register(KanbanColumn)
class KanbanColumnAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem', 'cor')
    search_fields = ('nome',)
    ordering = ('ordem',)

@admin.register(KanbanCard)
class KanbanCardAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'coluna', 'projeto', 'responsavel', 'prioridade', 'data_criacao')
    list_filter = ('coluna', 'prioridade', 'projeto', 'responsavel')
    search_fields = ('titulo', 'descricao')
    raw_id_fields = ('projeto', 'responsavel', 'membros', 'criado_por')
    date_hierarchy = 'data_criacao'
    list_per_page = 50
