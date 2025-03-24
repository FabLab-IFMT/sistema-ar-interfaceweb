from django.contrib import admin
from .models import Action, Event, LabSchedule

class ActionAdmin(admin.ModelAdmin):
    list_display = ('type', 'author', 'date', 'time', 'description', 'url')
    list_filter = ('date', 'type')
    search_fields = ('author', 'description', 'type', 'url')
    readonly_fields = ('date', 'time', 'ip_address', 'user_agent', 'error_traceback')
    date_hierarchy = 'date'
    list_per_page = 50

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('author', 'type', 'description')
        }),
        ('Detalhes Temporais', {
            'fields': ('date', 'time')
        }),
        ('Relacionamentos', {
            'fields': ('user',)
        }),
        ('Detalhes Técnicos', {
            'classes': ('collapse',),
            'fields': ('url', 'ip_address', 'user_agent', 'error_traceback'),
        }),
    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_time', 'end_time', 'approved', 'created_by')
    list_filter = ('event_type', 'approved', 'start_time')
    search_fields = ('title', 'description')
    filter_horizontal = ('participants',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é uma criação nova
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(LabSchedule)
class LabScheduleAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'opening_time', 'closing_time', 'is_closed')
    list_editable = ('opening_time', 'closing_time', 'is_closed')

# Registrar o ActionAdmin com filtros avançados
admin.site.register(Action, ActionAdmin)