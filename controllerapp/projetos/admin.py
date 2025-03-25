from django.contrib import admin
from .models import Projeto, ProjetoTag, ProjetoImagem

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
