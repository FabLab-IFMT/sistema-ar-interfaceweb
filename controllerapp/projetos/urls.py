from django.urls import path
from . import views

app_name = 'projetos'

urlpatterns = [
    path('', views.projeto_lista, name='lista'),
    path('<slug:slug>/', views.projeto_detalhe, name='detalhe'),
    path('comentario/<int:projeto_id>/adicionar/', views.adicionar_comentario, name='adicionar_comentario'),
    path('comentario/<int:comentario_id>/excluir/', views.excluir_comentario, name='excluir_comentario'),
]
