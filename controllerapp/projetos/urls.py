from django.urls import path
from . import views

app_name = 'projetos'

urlpatterns = [
    path('', views.projeto_lista, name='lista'),
    path('novo/', views.projeto_novo, name='novo'),  # Nova URL para criar projetos
    path('gestao/', views.gestao_projetos, name='gestao'),  # Hub de gestão de projetos
    path('gestao/<slug:slug>/', views.projeto_painel, name='projeto_painel'),  # Painel individual do projeto
    
    # Novas rotas para grupos de projeto
    path('grupos/', views.grupo_lista, name='grupos_lista'),
    path('grupos/novo/', views.grupo_novo, name='grupo_novo'),
    path('grupos/<int:grupo_id>/', views.grupo_detalhe, name='grupo_detalhe'),
    path('grupos/<int:grupo_id>/editar/', views.grupo_editar, name='grupo_editar'),
    path('grupos/<int:grupo_id>/excluir/', views.grupo_excluir, name='grupo_excluir'),
    
    path('todo/', views.todo_list, name='todo_list'),  # Rota para Todo List
    path('todo/add/', views.add_task, name='add_task'),  # Adicionar tarefa
    path('todo/<int:task_id>/update/', views.update_task, name='update_task'),  # Atualizar tarefa
    path('todo/<int:task_id>/delete/', views.delete_task, name='delete_task'),  # Excluir tarefa
    path('<int:projeto_id>/comentar/', views.adicionar_comentario, name='comentar'),
    path('comentario/<int:comentario_id>/excluir/', views.excluir_comentario, name='excluir_comentario'),
    path('<slug:slug>/', views.projeto_detalhe, name='detalhe'),  # Movido para o final
]
