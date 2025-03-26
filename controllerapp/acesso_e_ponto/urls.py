from django.urls import path
from .views import check_card, check_card_status, my_access_history, user_access_history, dashboard

app_name = 'acesso_e_ponto'

urlpatterns = [
    # Endpoints para ESP32
    path('verificar_cartao/', check_card, name='verificar_cartao'),
    path('status_cartao/', check_card_status, name='status_cartao'),
    
    # Interfaces web
    path('meus-acessos/', my_access_history, name='my_access_history'),
    path('usuario/<str:user_id>/acessos/', user_access_history, name='user_access_history'),
    path('dashboard/', dashboard, name='dashboard'),
]
