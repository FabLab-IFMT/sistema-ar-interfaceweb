from django.urls import path
from . import views

app_name = 'options'

urlpatterns = [
    path('equipamentos/', views.equipamentos, name='equipamentos'),
    path('membros/', views.membros, name='membros'),
]