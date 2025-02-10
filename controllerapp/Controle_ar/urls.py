from django.urls import path
from . import views
from users.views import login_view, logout_view, register_view  # Alterado de 'controllerapp.users.views'

app_name = 'Controle_ar'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', views.index, name='home'),


    
    # Adicionando paths para os comandos do ESP32
    path('ligar/', views.ligar, name='ligar'),
    path('desligar/', views.desligar, name='desligar'),
    path('aumentar/', views.aumentar, name='aumentar'),
    path('diminuir/', views.diminuir, name='diminuir'),
    path('definir_temperatura/', views.definir_temperatura, name='definir_temperatura'),
]