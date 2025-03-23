from django.urls import path
from . import views

app_name = 'options'

urlpatterns = [
    path('equipamentos/', views.equipamentos, name='equipamentos'),
    path('membros/', views.membros, name='membros'),
    path('servicos/', views.servicos, name='servicos'),
    path('servicos/<int:servico_id>/', views.detalhe_servico, name='detalhe_servico'),
    path('minhas-solicitacoes/', views.minhas_solicitacoes, name='minhas_solicitacoes'),
    path('solicitacao/<int:solicitacao_id>/', views.solicitacao_detalhe, name='solicitacao_detalhe'),
    
    # Novas URLs para o sistema de notícias
    path('noticias/', views.noticias_lista, name='noticias'),
    path('noticias/tag/<slug:slug>/', views.noticias_por_tag, name='noticias_por_tag'),
    path('noticias/<slug:slug>/', views.noticia_detalhe, name='noticia_detalhe'),
]