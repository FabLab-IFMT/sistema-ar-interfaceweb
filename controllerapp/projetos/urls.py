from django.urls import path
from . import views

app_name = 'projetos'

urlpatterns = [
    path('', views.projeto_lista, name='lista'),
    path('<slug:slug>/', views.projeto_detalhe, name='detalhe'),
]
