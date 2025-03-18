from django.contrib import admin
from .models import Material, Membro, CategoriaServico, Servico, ProjetoExemplo, SolicitacaoOrcamento

# Register your models here.
admin.site.register(Material)

@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'ativo', 'ordem')
    list_filter = ('ativo', 'cargo')
    search_fields = ('nome', 'email', 'bio')
    ordering = ('ordem', 'nome')
    list_editable = ('ordem', 'ativo')

@admin.register(CategoriaServico)
class CategoriaServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem')
    list_editable = ('ordem',)
    search_fields = ('nome',)

class ProjetoExemploInline(admin.TabularInline):
    model = ProjetoExemplo
    extra = 1

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco_base', 'disponivel', 'destaque', 'ordem')
    list_filter = ('categoria', 'disponivel', 'destaque')
    list_editable = ('disponivel', 'destaque', 'ordem')
    search_fields = ('nome', 'descricao', 'descricao_curta')
    inlines = [ProjetoExemploInline]

@admin.register(SolicitacaoOrcamento)
class SolicitacaoOrcamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'servico', 'status', 'data_solicitacao')
    list_filter = ('status', 'servico__categoria', 'servico')
    search_fields = ('nome', 'email', 'descricao_projeto')
    readonly_fields = ('data_solicitacao',)
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('usuario', 'nome', 'email', 'telefone')
        }),
        ('Informações do Serviço', {
            'fields': ('servico', 'descricao_projeto', 'arquivo_referencia')
        }),
        ('Status e Orçamento', {
            'fields': ('status', 'valor_orcado', 'observacoes_admin')
        }),
        ('Datas', {
            'fields': ('data_solicitacao',)
        }),
    )
