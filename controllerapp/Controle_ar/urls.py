from django.urls import path
from . import views

app_name = 'Controle_ar'

urlpatterns = [
    # Página inicial de automação
    path('', views.automacao_home, name='automacao_home'),
    
    # Páginas de ar-condicionado
    path('ar/', views.ar_dashboard, name='ar_dashboard'),
    path('ar/<int:ar_id>/', views.controlar_ar, name='controlar_ar'),
    
    # Comandos para controle de ar
    path('ar/<int:ar_id>/ligar/', views.ligar_ar, name='ligar_ar'),
    path('ar/<int:ar_id>/desligar/', views.desligar_ar, name='desligar_ar'),
    path('ar/<int:ar_id>/temperatura/', views.ajustar_temperatura, name='ajustar_temperatura'),
    path('ar/<int:ar_id>/modo/', views.ajustar_modo, name='ajustar_modo'),
    path('ar/<int:ar_id>/velocidade/', views.ajustar_velocidade, name='ajustar_velocidade'),
    path('ar/<int:ar_id>/swing/', views.toggle_swing, name='toggle_swing'),
    path('ar/<int:ar_id>/status/', views.verificar_status, name='verificar_status'),
    
    # API para o ESP32 se comunicar
    path('api/status/', views.api_status, name='api_status'),
    
    # Compatibilidade para URLs antigas
    path('dashboard/', views.dashboard, name='dashboard'),
]