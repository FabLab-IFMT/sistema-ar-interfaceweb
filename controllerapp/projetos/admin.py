from django.contrib import admin
from .models import Projeto, ProjetoTag, ProjetoImagem, ComentarioProjeto, TodoTask, ProjetoGrupo, ProjetoMarco

class ProjetoImagemInline(admin.TabularInline):
    model = ProjetoImagem
    extra = 1
    fields = ['titulo', 'imagem', 'legenda', 'ordem']

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'status', 'data_inicio', 'data_conclusao', 'mostrar_na_home', 'publicado', 'destaque')
    list_filter = ('status', 'mostrar_na_home', 'publicado', 'destaque', 'tags')
    search_fields = ('titulo', 'descricao', 'descricao_curta')
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'data_criacao'
    filter_horizontal = ('participantes', 'tags')
    list_editable = ('mostrar_na_home', 'publicado', 'destaque')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'slug', 'descricao_curta', 'descricao', 'imagem')
        }),
        ('Status e Datas', {
            'fields': ('status', 'data_inicio', 'data_conclusao')
        }),
        ('Equipe', {
            'fields': ('responsavel', 'participantes')
        }),
        ('Categorização', {
            'fields': ('tags',)
        }),
        ('Links Externos', {
            'fields': ('link_github', 'link_video', 'link_documentacao'),
            'classes': ('collapse',)
        }),
        ('Opções de Exibição', {
            'fields': ('mostrar_na_home', 'publicado', 'destaque')
        }),
    )
    
    inlines = [ProjetoImagemInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.responsavel:
            obj.responsavel = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProjetoTag)
class ProjetoTagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ('nome',)

@admin.register(ProjetoImagem)
class ProjetoImagemAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ordem')
    list_editable = ('ordem',)
    search_fields = ('titulo', 'legenda')

class ComentarioRespostaInline(admin.TabularInline):
    model = ComentarioProjeto
    fk_name = 'comentario_pai'
    extra = 1
    fields = ['autor', 'texto', 'aprovado', 'destacado']
    verbose_name = "Resposta"
    verbose_name_plural = "Respostas"

@admin.register(ComentarioProjeto)
class ComentarioProjetoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'autor', 'texto_truncado', 'is_resposta', 'aprovado', 'destacado', 'data_criacao')
    list_filter = ('aprovado', 'destacado', 'data_criacao')
    search_fields = ('texto', 'autor__username', 'autor__first_name', 'autor__last_name', 'projeto__titulo')
    date_hierarchy = 'data_criacao'
    list_editable = ('aprovado', 'destacado')
    inlines = [ComentarioRespostaInline]
    
    def texto_truncado(self, obj):
        """Retorna uma versão truncada do texto do comentário"""
        return obj.texto[:100] + '...' if len(obj.texto) > 100 else obj.texto
    texto_truncado.short_description = 'Texto'
    
    def get_queryset(self, request):
        """Mostra apenas comentários principais (não respostas) na listagem principal"""
        qs = super().get_queryset(request)
        if request.path.endswith('/change/'):
            return qs
        return qs.filter(comentario_pai__isnull=True)

@admin.register(TodoTask)
class TodoTaskAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'projeto', 'prioridade', 'data_limite', 'concluida')
    list_filter = ('concluida', 'prioridade', 'usuario', 'projeto')
    search_fields = ('titulo', 'descricao')
    date_hierarchy = 'data_criacao'


@admin.register(ProjetoMarco)
class ProjetoMarcoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'projeto', 'data', 'progresso', 'responsavel')
    list_filter = ('projeto',)
    search_fields = ('titulo', 'descricao', 'projeto__titulo')
    ordering = ('data', 'ordem')
    readonly_fields = ('criado_em', 'atualizado_em')

@admin.register(ProjetoGrupo)
class ProjetoGrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'get_membros_count', 'get_projetos_count', 'criado_por', 'data_criacao')
    search_fields = ('nome', 'descricao')
    filter_horizontal = ('membros', 'projetos')
    readonly_fields = ('criado_por', 'data_criacao', 'data_atualizacao')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao')
        }),
        ('Membros e Projetos', {
            'fields': ('membros', 'projetos')
        }),
        ('Informações do Sistema', {
            'fields': ('criado_por', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def get_membros_count(self, obj):
        return obj.membros.count()
    get_membros_count.short_description = 'Membros'
    
    def get_projetos_count(self, obj):
        return obj.projetos.count()
    get_projetos_count.short_description = 'Projetos'
    
    def save_model(self, request, obj, form, change):
        if not obj.criado_por:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        # Apenas superusuários podem adicionar grupos
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Apenas superusuários podem editar grupos
        return request.user.is_superuser
