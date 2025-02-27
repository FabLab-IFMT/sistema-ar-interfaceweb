from django.contrib import admin
from .models import Action, Event, LabSchedule

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('type', 'author', 'date', 'time')
    list_filter = ('date', 'type')
    search_fields = ('author', 'description', 'type')

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