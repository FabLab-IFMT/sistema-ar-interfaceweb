from django.urls import path
from . import views

app_name = 'cursos'

urlpatterns = [
    # ── Públicas ──
    path('', views.curso_lista, name='lista'),

    # ── Admin / Gestão ──
    path('admin/', views.admin_cursos, name='admin_cursos'),
    path('admin/novo/', views.admin_curso_form, name='admin_curso_novo'),
    path('admin/<int:curso_id>/editar/', views.admin_curso_form, name='admin_curso_editar'),
    path('admin/<int:curso_id>/toggle-publicado/', views.admin_curso_toggle_publicado, name='admin_curso_toggle_publicado'),
    path('admin/<int:curso_id>/deletar/', views.admin_curso_deletar, name='admin_curso_deletar'),

    # ── Detalhe público (por último para não capturar as rotas admin) ──
    path('<slug:slug>/', views.curso_detalhe, name='detalhe'),
]
