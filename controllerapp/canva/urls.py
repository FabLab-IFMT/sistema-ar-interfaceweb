from django.urls import path
from . import views

app_name = 'canva'

urlpatterns = [
    # View principal do Kanban
    path('', views.kanban_view, name='kanban'),
    
    # APIs para manipulação dos cards
    path('card/add/', views.add_card, name='add_card'),
    path('card/move/', views.move_card, name='move_card'),
    path('card/<int:card_id>/', views.card_details, name='card_details'),
    path('card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    
    # APIs para manipulação das colunas (apenas superuser)
    path('column/add/', views.add_column, name='add_column'),
    path('column/<int:column_id>/', views.edit_column, name='edit_column'),  # Nova URL
    path('column/<int:column_id>/delete/', views.delete_column, name='delete_column'),
    path('column/reorder/', views.reorder_columns, name='reorder_columns'),
]
