from django.urls import path
from . import views

app_name = 'projetos'

urlpatterns = [
    path('', views.projeto_lista, name='projeto_lista'),
    path('<slug:slug>/', views.projeto_detalhe, name='projeto_detalhe'),
]
