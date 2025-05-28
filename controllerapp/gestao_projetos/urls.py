from django.urls import path
from . import views

app_name = 'gestao_projetos'

urlpatterns = [
    # URLs para grupos de projetos
    path('grupos/', views.lista_grupos_projetos, name='lista_grupos_projetos'),
    path('grupos/criar/', views.criar_grupo_projetos, name='criar_grupo_projetos'),
    path('grupos/<slug:slug>/', views.detalhes_grupo_projetos, name='detalhes_grupo_projetos'),
    path('grupos/<slug:slug>/editar/', views.editar_grupo_projetos, name='editar_grupo_projetos'),
    path('grupos/<slug:slug>/excluir/', views.excluir_grupo_projetos, name='excluir_grupo_projetos'),
]