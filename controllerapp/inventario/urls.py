from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Dashboard
    path('', views.inventario_dashboard, name='dashboard'),
    
    # Itens
    path('itens/', views.item_list, name='item_list'),
    path('itens/novo/', views.item_create, name='item_create'),
    path('itens/<int:pk>/', views.item_detail, name='item_detail'),
    path('itens/<int:pk>/editar/', views.item_update, name='item_update'),
    path('itens/<int:pk>/excluir/', views.item_delete, name='item_delete'),
    path('itens/criticos/', views.itens_criticos, name='itens_criticos'),
    
    # Categorias
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categorias/nova/', views.categoria_create, name='categoria_create'),
    
    # Empréstimos
    path('emprestimos/', views.emprestimo_list, name='emprestimo_list'),
    path('emprestimos/novo/', views.emprestimo_create, name='emprestimo_create'),
    path('emprestimos/<int:pk>/', views.emprestimo_detail, name='emprestimo_detail'),
    path('emprestimos/<int:pk>/devolucao/', views.emprestimo_devolucao, name='emprestimo_devolucao'),
]
