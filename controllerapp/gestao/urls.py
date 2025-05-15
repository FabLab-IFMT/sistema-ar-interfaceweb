from django.urls import path
from . import views

app_name = 'gestao'

urlpatterns = [
    path('', views.dashboard_gestao, name='dashboard'),
    path('acessos/', views.gerenciar_acessos, name='gerenciar_acessos'),
    path('acessos/toggle/<int:user_id>/', views.toggle_acesso, name='toggle_acesso'),
    path('monitoramento/', views.monitoramento_sistema, name='monitoramento'),
    path('configuracoes/', views.configuracoes_sistema, name='configuracoes'),
]