from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.logs_list, name='index'),
    path('log/<int:day>/<int:month>/<int:year>/', views.logs_datepage, name='datepage'),
    
    # URLs para a agenda
    path('agenda/', views.agenda_home, name='agenda_home'),
    path('agenda/evento/<int:event_id>/', views.agenda_event_detail, name='agenda_event_detail'),
    path('agenda/criar/', views.agenda_create_event, name='agenda_create_event'), 
    path('agenda/solicitar-visita/', views.agenda_request_visit, name='request_visit'),
    path('agenda/aprovar/<int:event_id>/', views.agenda_approve_event, name='agenda_approve_event'),
    path('agenda/aprovar/<int:event_id>/', views.agenda_approve_event, name='approve_event'),  # Alias para URLs antigas
    path('agenda/excluir/<int:event_id>/', views.agenda_delete_event, name='agenda_delete_event'),
    path('agenda/excluir/<int:event_id>/', views.agenda_delete_event, name='delete_event'),  # Alias para URLs antigas
    path('agenda/rejeitar/<int:event_id>/', views.agenda_reject_event, name='agenda_reject_event'),
    path('agenda/pendentes/', views.pending_events, name='pending_events'),
]