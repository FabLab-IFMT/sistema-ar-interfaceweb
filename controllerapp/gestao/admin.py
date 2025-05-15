from django.contrib import admin
from .models import AcessoGestao

@admin.register(AcessoGestao)
class AcessoGestaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tem_acesso', 'concedido_por', 'data_concessao', 'ultima_modificacao')
    list_filter = ('tem_acesso',)
    search_fields = ('usuario__username', 'usuario__email', 'usuario__first_name', 'usuario__last_name')
    date_hierarchy = 'data_concessao'
    readonly_fields = ('concedido_por', 'data_concessao', 'ultima_modificacao')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo registro
            obj.concedido_por = request.user
        super().save_model(request, obj, form, change)
