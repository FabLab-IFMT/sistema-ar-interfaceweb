from django.urls import path

from . import views

# Endpoints consumidos pelo ESP32 da estufa.
# Ficam fora de /painelar/ de propósito: o firmware em produção
# aponta para /estufa/api/... e não deve quebrar.
app_name = 'estufa_api'

urlpatterns = [
    path('telemetria/', views.api_telemetria, name='telemetria'),
    path('comandos/', views.api_comandos, name='comandos'),
]
