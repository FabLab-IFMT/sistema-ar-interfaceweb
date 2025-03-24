from django.contrib import admin
from django.contrib.admin.models import LogEntry
from .models import Action, Event, LabSchedule
from .utils import log_user_action

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'type', 'author', 'severity', 'url')
    list_filter = ('date', 'type', 'severity')
    search_fields = ('author', 'description', 'type', 'url')
    date_hierarchy = 'date'
    readonly_fields = ('date', 'time', 'author', 'type', 'description', 'url', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        # Impedir adição manual de logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Impedir modificação de logs
        return False

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_time', 'end_time', 'approved', 'created_by')
    list_filter = ('event_type', 'approved', 'start_time')
    search_fields = ('title', 'description')
    filter_horizontal = ('participants',)
    
    def save_model(self, request, obj, form, change):
        # Registrar a criação ou modificação do evento
        if not change:  # Se é uma criação nova
            obj.created_by = request.user
            action_type = 'Criação de Evento'
            action_desc = f"Criou o evento '{obj.title}'"
        else:
            action_type = 'Modificação de Evento'
            action_desc = f"Modificou o evento '{obj.title}'"
        
        super().save_model(request, obj, form, change)
        
        # Registrar a ação
        log_user_action(
            user=request.user,
            action_type=action_type,
            description=action_desc,
            severity='info',
            request=request
        )
    
    def delete_model(self, request, obj):
        # Registrar a exclusão do evento
        action_type = 'Exclusão de Evento'
        action_desc = f"Excluiu o evento '{obj.title}'"
        
        super().delete_model(request, obj)
        
        # Registrar a ação
        log_user_action(
            user=request.user,
            action_type=action_type,
            description=action_desc,
            severity='info',
            request=request
        )

@admin.register(LabSchedule)
class LabScheduleAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'opening_time', 'closing_time', 'is_closed')
    list_editable = ('opening_time', 'closing_time', 'is_closed')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Registrar alteração no horário
        action_type = 'Alteração de Horário'
        action_desc = f"Modificou o horário de funcionamento para {obj.get_day_of_week_display()}"
        
        # Registrar a ação
        log_user_action(
            user=request.user,
            action_type=action_type,
            description=action_desc,
            severity='info',
            request=request
        )