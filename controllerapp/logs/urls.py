from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    # URLs para logs (acesso admin)
    path('admin/', views.logs_list, name='list'),
    path('admin/<int:day>/<int:month>/<int:year>', views.logs_datepage, name='datepage'),
    
    # URLs para agenda (acesso público)
    path('', views.agenda_home, name='agenda_home'),
    path('evento/<int:event_id>/', views.agenda_event_detail, name='event_detail'),
    path('criar-evento/', views.agenda_create_event, name='create_event'),
    path('agendar-visita/', views.agenda_request_visit, name='request_visit'),
    
    # URLs para administração de agenda (acesso admin)
    path('pendentes/', views.pending_events, name='pending_events'),
    path('aprovar-evento/<int:event_id>/', views.agenda_approve_event, name='approve_event'),
    path('excluir-evento/<int:event_id>/', views.agenda_delete_event, name='delete_event'),
]