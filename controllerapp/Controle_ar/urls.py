from django.urls import path
from . import views

app_name = 'Controle_ar'

urlpatterns = [
    # Página principal de automação
    path('', views.automacao_home, name='automacao_home'),
    
    # Dashboard de ar-condicionado
    path('ar/', views.ar_dashboard, name='ar_dashboard'),
    
    # Manter compatibilidade com links antigos
    path('dashboard/', views.ar_dashboard, name='dashboard'),
    
    # Demais URLs permanecem iguais
    path('controlar/<int:ar_id>/', views.controlar_ar, name='controlar_ar'),
    path('ligar/<int:ar_id>/', views.ligar_ar, name='ligar_ar'),
    path('desligar/<int:ar_id>/', views.desligar_ar, name='desligar_ar'),
    path('temperatura/<int:ar_id>/', views.ajustar_temperatura, name='ajustar_temperatura'),
    path('modo/<int:ar_id>/', views.ajustar_modo, name='ajustar_modo'),
    path('velocidade/<int:ar_id>/', views.ajustar_velocidade, name='ajustar_velocidade'),
    path('swing/<int:ar_id>/', views.toggle_swing, name='toggle_swing'),
    path('api/status/', views.api_status, name='api_status'),
]