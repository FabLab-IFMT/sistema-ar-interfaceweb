from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import WeeklyRequiredHours, TimeLog, Session

@admin.register(WeeklyRequiredHours)
class WeeklyRequiredHoursAdmin(admin.ModelAdmin):
    list_display = ('user', 'required_hours', 'last_modified', 'modified_by')
    list_filter = ('required_hours',)
    search_fields = ('user__first_name', 'user__last_name', 'user__id')
    autocomplete_fields = ['user', 'modified_by']
    
    # Todos com is_staff têm acesso à visualização e edição
    # O gerenciamento específico será feito via grupos e permissões pelo superuser
    
    def save_model(self, request, obj, form, change):
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'status', 'registered_by_card')
    list_filter = ('status', 'timestamp', 'user')
    search_fields = ('user__first_name', 'user__last_name', 'user__id')
    date_hierarchy = 'timestamp'
    autocomplete_fields = ['user']
    readonly_fields = ('timestamp', 'registered_by_card')
    
    # Sem restrições de permissão - qualquer is_staff pode visualizar e editar
    # O gerenciamento de permissões será feito via grupos

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'entry_time', 'exit_time', 'get_duration', 'is_active')
    list_filter = ('is_active', 'entry_time', 'user')
    search_fields = ('user__first_name', 'user__last_name', 'user__id')
    date_hierarchy = 'entry_time'
    autocomplete_fields = ['user']
    readonly_fields = ('duration',)
    actions = ['close_active_sessions']
    
    # Sem restrições de permissão - qualquer is_staff pode visualizar e editar
    # O gerenciamento de permissões será feito via grupos
    
    def get_duration(self, obj):
        if obj.duration:
            total_seconds = obj.duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}min"
        elif obj.is_active:
            total_seconds = obj.calculate_duration().total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}min (Ativa)"
        return "Sem duração"
    get_duration.short_description = _("Duração")
    
    def close_active_sessions(self, request, queryset):
        closed = 0
        for session in queryset.filter(is_active=True):
            if session.close_session():
                closed += 1
        if closed:
            self.message_user(request, f"{closed} sessões foram fechadas com sucesso.")
        else:
            self.message_user(request, "Nenhuma sessão ativa foi encontrada.")
    close_active_sessions.short_description = _("Fechar sessões ativas selecionadas")
