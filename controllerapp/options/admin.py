from django.contrib import admin
from .models import Material, Membro, CategoriaServico, Servico, ProjetoExemplo, SolicitacaoOrcamento, Noticia, Hashtag

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

@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ('nome',)

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_publicacao', 'publicado', 'mostrar_na_home', 'destaque', 'get_hashtags')
    list_filter = ('publicado', 'mostrar_na_home', 'destaque', 'hashtags')
    search_fields = ('titulo', 'resumo', 'conteudo')
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'data_publicacao'
    list_editable = ('publicado', 'mostrar_na_home', 'destaque')
    filter_horizontal = ('hashtags',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'slug', 'resumo', 'conteudo', 'imagem', 'autor')
        }),
        ('Categorização', {
            'fields': ('hashtags',),
        }),
        ('Opções de Publicação', {
            'fields': ('publicado', 'mostrar_na_home', 'destaque')
        }),
    )
    
    def get_hashtags(self, obj):
        return ", ".join([tag.nome for tag in obj.hashtags.all()])
    get_hashtags.short_description = "Hashtags"
    
    def save_model(self, request, obj, form, change):
        if not obj.autor:
            obj.autor = request.user
        super().save_model(request, obj, form, change)
