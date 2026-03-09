from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

router = DefaultRouter()

# Users
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'roles', views.RoleViewSet, basename='role')
router.register(r'registration-requests', views.RegistrationRequestViewSet, basename='registration-request')
router.register(r'projectist-requests', views.ProjectistRequestViewSet, basename='projectist-request')

# Gestão
router.register(r'acessos-gestao', views.AcessoGestaoViewSet, basename='acesso-gestao')
router.register(r'configuracoes', views.ConfiguracaoViewSet, basename='configuracao')

# Options
router.register(r'materiais', views.MaterialViewSet, basename='material')
router.register(r'membros', views.MembroViewSet, basename='membro')
router.register(r'categorias-servico', views.CategoriaServicoViewSet, basename='categoria-servico')
router.register(r'servicos', views.ServicoViewSet, basename='servico')
router.register(r'hashtags', views.HashtagViewSet, basename='hashtag')
router.register(r'solicitacoes-interesse', views.SolicitacaoInteresseViewSet, basename='solicitacao-interesse')
router.register(r'noticias', views.NoticiaViewSet, basename='noticia')

# Inventário
router.register(r'categorias-inventario', views.CategoriaInventarioViewSet, basename='categoria-inventario')
router.register(r'itens', views.ItemViewSet, basename='item')
router.register(r'emprestimos', views.EmprestimoViewSet, basename='emprestimo')

# Projetos
router.register(r'projeto-tags', views.ProjetoTagViewSet, basename='projeto-tag')
router.register(r'projetos', views.ProjetoViewSet, basename='projeto')
router.register(r'comentarios-projeto', views.ComentarioProjetoViewSet, basename='comentario-projeto')
router.register(r'grupos-projeto', views.ProjetoGrupoViewSet, basename='grupo-projeto')
router.register(r'todo-tasks', views.TodoTaskViewSet, basename='todo-task')

# Logs
router.register(r'logs', views.ActionViewSet, basename='log')
router.register(r'eventos', views.EventViewSet, basename='evento')
router.register(r'horarios', views.LabScheduleViewSet, basename='horario')

# Controle AR
router.register(r'carousel', views.CarouselImageViewSet, basename='carousel')
router.register(r'ar-condicionados', views.ArCondicionadoViewSet, basename='ar-condicionado')
router.register(r'comandos-ar', views.ComandoArViewSet, basename='comando-ar')

# Canva (Kanban)
router.register(r'kanban-columns', views.KanbanColumnViewSet, basename='kanban-column')
router.register(r'kanban-cards', views.KanbanCardViewSet, basename='kanban-card')

# Repositório
router.register(r'categorias-recurso', views.ResourceCategoryViewSet, basename='categoria-recurso')
router.register(r'recursos', views.ResourceViewSet, basename='recurso')
router.register(r'resource-files', views.ResourceFileViewSet, basename='resource-file')
router.register(r'resource-comments', views.ResourceCommentViewSet, basename='resource-comment')

# Acesso e Ponto
router.register(r'weekly-hours', views.WeeklyRequiredHoursViewSet, basename='weekly-hours')
router.register(r'time-logs', views.TimeLogViewSet, basename='time-log')
router.register(r'sessions', views.SessionViewSet, basename='session')

app_name = 'api'

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Perfil do usuário autenticado
    path('me/', views.UserProfileView.as_view(), name='user-profile'),

    # Dashboard de gestão
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Todas as rotas do router
    path('', include(router.urls)),
]
