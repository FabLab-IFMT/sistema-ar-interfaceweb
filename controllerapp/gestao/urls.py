from django.urls import path
from . import views

app_name = 'gestao'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_gestao, name='dashboard'),

    # Monitoramento
    path('monitoramento/', views.monitoramento_sistema, name='monitoramento'),

    # Acessos à gestão
    path('acessos/', views.gerenciar_acessos, name='gerenciar_acessos'),
    path('acessos/toggle/<str:user_id>/', views.toggle_acesso, name='toggle_acesso'),

    # ── Admin Usuários ──
    path('usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('usuarios/<str:user_id>/editar/', views.admin_usuario_editar, name='admin_usuario_editar'),
    path('usuarios/<str:user_id>/toggle-ativo/', views.admin_usuario_toggle_ativo, name='admin_usuario_toggle_ativo'),
    path('usuarios/<str:user_id>/toggle-staff/', views.admin_usuario_toggle_staff, name='admin_usuario_toggle_staff'),

    # ── Admin Conteúdo ──
    path('conteudo/', views.admin_conteudo, name='admin_conteudo'),

    # Notícias
    path('conteudo/noticias/', views.admin_noticias, name='admin_noticias'),
    path('conteudo/noticias/nova/', views.admin_noticia_form, name='admin_noticia_nova'),
    path('conteudo/noticias/<int:noticia_id>/editar/', views.admin_noticia_form, name='admin_noticia_editar'),
    path('conteudo/noticias/<int:noticia_id>/deletar/', views.admin_noticia_deletar, name='admin_noticia_deletar'),
    path('conteudo/noticias/<int:noticia_id>/toggle-publicado/', views.admin_noticia_toggle_publicado, name='admin_noticia_toggle_publicado'),
    path('conteudo/noticias/<int:noticia_id>/toggle-destaque/', views.admin_noticia_toggle_destaque, name='admin_noticia_toggle_destaque'),
    path('conteudo/noticias/foto/<int:foto_id>/deletar/', views.admin_noticia_foto_deletar, name='admin_noticia_foto_deletar'),

    # Membros
    path('conteudo/membros/', views.admin_membros, name='admin_membros'),
    path('conteudo/membros/novo/', views.admin_membro_form, name='admin_membro_novo'),
    path('conteudo/membros/<int:membro_id>/editar/', views.admin_membro_form, name='admin_membro_editar'),
    path('conteudo/membros/<int:membro_id>/deletar/', views.admin_membro_deletar, name='admin_membro_deletar'),
    path('conteudo/membros/<int:membro_id>/toggle-ativo/', views.admin_membro_toggle_ativo, name='admin_membro_toggle_ativo'),

    # Serviços
    path('conteudo/servicos/', views.admin_servicos, name='admin_servicos'),
    path('conteudo/servicos/novo/', views.admin_servico_form, name='admin_servico_novo'),
    path('conteudo/servicos/<int:servico_id>/editar/', views.admin_servico_form, name='admin_servico_editar'),
    path('conteudo/servicos/<int:servico_id>/deletar/', views.admin_servico_deletar, name='admin_servico_deletar'),
    path('conteudo/servicos/<int:servico_id>/toggle-disponivel/', views.admin_servico_toggle_disponivel, name='admin_servico_toggle_disponivel'),

    # Solicitações de interesse
    path('conteudo/solicitacoes/', views.admin_solicitacoes, name='admin_solicitacoes'),
    path('conteudo/solicitacoes/<int:sol_id>/status/', views.admin_solicitacao_status, name='admin_solicitacao_status'),

    # ── Admin Inventário (overview rápido) ──
    path('inventario/', views.admin_inventario_overview, name='admin_inventario'),

    # ── Configurações ──
    path('configuracoes/', views.configuracoes_sistema, name='configuracoes'),
]
