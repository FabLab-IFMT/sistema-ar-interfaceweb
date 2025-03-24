from django.contrib import admin
from .models import Categoria, Item, Emprestimo

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'categoria', 'quantidade', 'unidade', 'valor_unitario', 'estoque_baixo')
    list_filter = ('categoria',)
    search_fields = ('codigo', 'nome', 'descricao')
    readonly_fields = ('data_cadastro', 'data_atualizacao')

@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('item', 'usuario', 'quantidade', 'data_emprestimo', 'data_prevista_devolucao', 'data_devolucao', 'status')
    list_filter = ('data_emprestimo', 'data_devolucao')
    search_fields = ('item__nome', 'usuario__first_name', 'usuario__last_name', 'usuario__email')
    date_hierarchy = 'data_emprestimo'
    readonly_fields = ('status',)
