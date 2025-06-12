from django.urls import path
from . import views

app_name = 'Controle_ar'

urlpatterns = [
    # Página inicial de automação
    path('', views.automacao_home, name='automacao_home'),
    
    # Páginas de ar-condicionado
    path('ar/', views.ar_dashboard, name='ar_dashboard'),
    path('ar/<int:ar_id>/', views.controlar_ar, name='controlar_ar'),
    
    # Comandos para controle de ar (tradicionais)
    path('ar/<int:ar_id>/ligar/', views.ligar_ar, name='ligar_ar'),
    path('ar/<int:ar_id>/desligar/', views.desligar_ar, name='desligar_ar'),
    path('ar/<int:ar_id>/temperatura/', views.ajustar_temperatura, name='ajustar_temperatura'),
    path('ar/<int:ar_id>/modo/', views.ajustar_modo, name='ajustar_modo'),
    path('ar/<int:ar_id>/velocidade/', views.ajustar_velocidade, name='ajustar_velocidade'),
    path('ar/<int:ar_id>/swing/', views.toggle_swing, name='toggle_swing'),
    path('ar/<int:ar_id>/status/', views.verificar_status, name='verificar_status'),
    
    # Comandos para controle de ar (AJAX)
    path('ar/<int:ar_id>/ligar/ajax/', views.ligar_ar_ajax, name='ligar_ar_ajax'),
    path('ar/<int:ar_id>/desligar/ajax/', views.desligar_ar_ajax, name='desligar_ar_ajax'),
    path('ar/<int:ar_id>/temperatura/ajax/', views.ajustar_temperatura_ajax, name='ajustar_temperatura_ajax'),
    path('ar/<int:ar_id>/modo/ajax/', views.ajustar_modo_ajax, name='ajustar_modo_ajax'),
    path('ar/<int:ar_id>/velocidade/ajax/', views.ajustar_velocidade_ajax, name='ajustar_velocidade_ajax'),
    path('ar/<int:ar_id>/swing/ajax/', views.toggle_swing_ajax, name='toggle_swing_ajax'),
    path('ar/<int:ar_id>/status/ajax/', views.verificar_status_ajax, name='verificar_status_ajax'),
    
    # API para o ESP32 se comunicar
    path('api/status/', views.api_status, name='api_status'),
    
    # Compatibilidade para URLs antigas
    path('dashboard/', views.dashboard, name='dashboard'),
]