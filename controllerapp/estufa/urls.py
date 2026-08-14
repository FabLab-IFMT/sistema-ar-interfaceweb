from django.urls import path

from . import views

app_name = 'estufa'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('<int:estufa_id>/', views.detalhe, name='detalhe'),
    path('<int:estufa_id>/modo/', views.definir_modo, name='definir_modo'),
    path('<int:estufa_id>/status/ajax/', views.status_ajax, name='status_ajax'),

    # API para o ESP32 da estufa se comunicar
    path('api/telemetria/', views.api_telemetria, name='api_telemetria'),
]
