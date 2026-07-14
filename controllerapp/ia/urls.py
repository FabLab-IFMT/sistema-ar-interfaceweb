from django.urls import path

from . import views

app_name = 'ia'

urlpatterns = [
    path('', views.painel_insights, name='painel'),
    path('gerar/', views.gerar, name='gerar'),
    path('<int:insight_id>/', views.detalhe, name='detalhe'),
    path('<int:insight_id>/excluir/', views.excluir, name='excluir'),
]
