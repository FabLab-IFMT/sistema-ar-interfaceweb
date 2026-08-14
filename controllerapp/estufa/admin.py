from django.contrib import admin

from .models import Estufa, LeituraEstufa, LogOperacaoEstufa


@admin.register(Estufa)
class EstufaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modo_desejado', 'modo_atual', 'estado',
                    'temperatura_media', 'umidade_media', 'ultimo_contato')
    readonly_fields = ('modo_atual', 'estado', 'temperatura_media', 'umidade_media',
                       'lampada_ligada', 'cooler_ligado', 'ultimo_contato')


@admin.register(LeituraEstufa)
class LeituraEstufaAdmin(admin.ModelAdmin):
    list_display = ('estufa', 'data_hora', 'modo', 'estado',
                    'temperatura_media', 'umidade_media', 'lampada_ligada', 'cooler_ligado')
    list_filter = ('estufa', 'modo', 'estado')
    date_hierarchy = 'data_hora'


@admin.register(LogOperacaoEstufa)
class LogOperacaoEstufaAdmin(admin.ModelAdmin):
    list_display = ('estufa', 'operacao', 'usuario', 'data_hora')
    list_filter = ('estufa',)
