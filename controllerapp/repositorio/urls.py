from django.urls import path
from . import views

app_name = 'repositorio'

urlpatterns = [
    # Página inicial do repositório
    path('', views.index, name='index'),
    
    # Recursos de um projeto específico
    path('projeto/<slug:project_slug>/', views.project_resources, name='project_resources'),
    
    # Criar recurso
    path('criar/', views.resource_create, name='resource_create'),
    path('projeto/<slug:project_slug>/criar/', views.resource_create, name='project_resource_create'),
    
    # Detalhes, edição e exclusão de recurso
    path('recurso/<slug:slug>/', views.resource_detail, name='resource_detail'),
    path('recurso/<slug:slug>/editar/', views.resource_edit, name='resource_edit'),
    path('recurso/<slug:slug>/excluir/', views.resource_delete, name='resource_delete'),
    
    # Download de arquivo
    path('arquivo/<int:file_id>/download/', views.download_file, name='download_file'),
    path('arquivo/<int:file_id>/excluir/', views.resource_file_delete, name='resource_file_delete'),
    
    # Comentários
    path('comentario/adicionar/<int:resource_id>/', views.add_comment, name='add_comment'),
    path('comentario/<int:comment_id>/excluir/', views.delete_comment, name='delete_comment'),
]
