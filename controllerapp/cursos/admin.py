from django.contrib import admin
from .models import Curso, CategoriaCurso


@admin.register(CategoriaCurso)
class CategoriaCursoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'icone', 'ordem')
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ('ordem', 'nome')


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'instrutor', 'status', 'publicado', 'destaque', 'criado_em')
    list_filter = ('status', 'publicado', 'destaque', 'mostrar_na_home', 'categoria')
    search_fields = ('titulo', 'descricao_curta', 'descricao')
    prepopulated_fields = {'slug': ('titulo',)}
    autocomplete_fields = ('projetos_relacionados',)
    date_hierarchy = 'criado_em'
    readonly_fields = ('criado_em', 'atualizado_em', 'criado_por')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

