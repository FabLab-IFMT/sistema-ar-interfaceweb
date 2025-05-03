from django.urls import path
from . import views

app_name = 'repositorio'

urlpatterns = [
    # Visualização principal
    path('', views.index, name='index'),
    
    # Recursos por projeto
    path('projeto/<slug:project_slug>/', views.project_resources, name='project_resources'),
    
    # Criar recurso (com ou sem projeto pré-selecionado)
    path('criar/', views.resource_create, name='resource_create'),
    path('projeto/<slug:project_slug>/criar/', views.resource_create, name='project_resource_create'),
    
    # Detalhes, edição e exclusão de recursos
    path('recurso/<slug:slug>/', views.resource_detail, name='resource_detail'),
    path('recurso/<slug:slug>/editar/', views.resource_edit, name='resource_edit'),
    path('recurso/<slug:slug>/excluir/', views.resource_delete, name='resource_delete'),
    
    # Comentários
    path('comentario/<int:comment_id>/excluir/', views.comment_delete, name='comment_delete'),
]
