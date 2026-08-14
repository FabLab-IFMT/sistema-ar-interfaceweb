from django.urls import path

from . import views

app_name = 'estufa'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('<int:estufa_id>/', views.detalhe, name='detalhe'),
    path('<int:estufa_id>/modo/', views.definir_modo, name='definir_modo'),
    path('<int:estufa_id>/controle/', views.definir_controle, name='definir_controle'),
    path('<int:estufa_id>/atuador/', views.definir_atuador, name='definir_atuador'),
    path('<int:estufa_id>/parametros/', views.definir_parametros, name='definir_parametros'),
    path('<int:estufa_id>/status/ajax/', views.status_ajax, name='status_ajax'),
]
