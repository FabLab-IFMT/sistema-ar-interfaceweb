from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .permissions import IsStaffOrReadOnly, IsSuperUser, IsGestaoAuthorized, IsOwnerOrStaff
from .serializers import (
    # Users
    RoleSerializer, UserSerializer, UserProfileSerializer, CardSerializer,
    RegistrationRequestSerializer, ProjectistRequestSerializer,
    # Gestão
    AcessoGestaoSerializer, ConfiguracaoSerializer,
    # Options
    MaterialSerializer, MembroSerializer, CategoriaServicoSerializer,
    ServicoSerializer, ProjetoExemploSerializer, HashtagSerializer,
    SolicitacaoInteresseSerializer, NoticiaSerializer,
    # Inventário
    CategoriaInventarioSerializer, ItemSerializer, EmprestimoSerializer,
    # Projetos
    ProjetoTagSerializer, ProjetoSerializer, ProjetoImagemSerializer,
    ComentarioProjetoSerializer, ProjetoGrupoSerializer, TodoTaskSerializer,
    # Logs
    ActionSerializer, EventSerializer, LabScheduleSerializer,
    # Controle AR
    CarouselImageSerializer, ArCondicionadoSerializer,
    ComandoArSerializer, LogOperacaoSerializer,
    # Canva (Kanban)
    KanbanColumnSerializer, KanbanCardSerializer,
    # Repositório
    ResourceCategorySerializer, ResourceSerializer,
    ResourceFileSerializer, ResourceCommentSerializer,
    # Acesso e Ponto
    WeeklyRequiredHoursSerializer, TimeLogSerializer, SessionSerializer,
)

# Models
from users.models import Role, CustomUser, Card, RegistrationRequest, ProjectistRequest
from gestao.models import AcessoGestao, Configuracao
from options.models import (
    Material, Membro, CategoriaServico, Servico, ProjetoExemplo,
    SolicitacaoInteresse, Hashtag, Noticia,
)
from inventario.models import Categoria as CategoriaInventario, Item, Emprestimo
from projetos.models import (
    ProjetoTag, Projeto, ProjetoImagem, ComentarioProjeto,
    ProjetoGrupo, TodoTask,
)
from logs.models import Action, Event, LabSchedule
from Controle_ar.models import CarouselImage, Ar_condicionado, Comando_ar, LogOperacao
from canva.models import KanbanColumn, KanbanCard
from repositorio.models import ResourceCategory, Resource, ResourceFile, ResourceComment
from acesso_e_ponto.models import WeeklyRequiredHours, TimeLog, Session

User = get_user_model()


# =============================================================================
# PERFIL DO USUÁRIO AUTENTICADO
# =============================================================================

class UserProfileView(APIView):
    """Retorna e permite editar o perfil do usuário autenticado (/api/me/)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# =============================================================================
# DASHBOARD DE GESTÃO
# =============================================================================

class DashboardView(APIView):
    """Retorna estatísticas consolidadas do sistema para o dashboard."""
    permission_classes = [IsGestaoAuthorized]

    def get(self, request):
        data_inicio = timezone.now() - timedelta(days=7)

        stats = {
            'usuarios': {
                'total': User.objects.count(),
                'ativos': User.objects.filter(is_active=True).count(),
                'staff': User.objects.filter(is_staff=True).count(),
                'superusers': User.objects.filter(is_superuser=True).count(),
            },
            'projetos': {
                'total': Projeto.objects.count(),
                'em_andamento': Projeto.objects.filter(status='em_andamento').count(),
                'concluidos': Projeto.objects.filter(status='concluido').count(),
            },
            'inventario': {
                'total_itens': Item.objects.count(),
                'estoque_baixo': self._estoque_baixo_count(),
                'emprestimos_ativos': Emprestimo.objects.filter(
                    data_devolucao__isnull=True
                ).count(),
            },
            'eventos': {
                'pendentes': Event.objects.filter(approved=False).count(),
                'proximos': Event.objects.filter(
                    start_time__gte=timezone.now(),
                    approved=True,
                ).count(),
            },
            'noticias_recentes': NoticiaSerializer(
                Noticia.objects.order_by('-data_publicacao')[:5],
                many=True,
            ).data,
            'logs_recentes': ActionSerializer(
                Action.objects.filter(
                    date__gte=data_inicio.date()
                ).order_by('-date', '-time')[:10],
                many=True,
            ).data,
        }
        return Response(stats)

    def _estoque_baixo_count(self):
        count = 0
        for item in Item.objects.all():
            if item.estoque_baixo:
                count += 1
        return count


# =============================================================================
# USERS
# =============================================================================

class UserViewSet(viewsets.ModelViewSet):
    """CRUD de usuários. Staff pode listar todos; usuário normal só vê o próprio."""
    queryset = User.objects.all().prefetch_related('roles')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['first_name', 'date_joined']

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    search_fields = ['name', 'code']


class RegistrationRequestViewSet(viewsets.ModelViewSet):
    queryset = RegistrationRequest.objects.all().order_by('-created_at')
    serializer_class = RegistrationRequestSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        reg = self.get_object()
        reg.status = 'approved'
        reg.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        reg = self.get_object()
        reg.status = 'rejected'
        reg.save()
        return Response({'status': 'rejected'})


class ProjectistRequestViewSet(viewsets.ModelViewSet):
    queryset = ProjectistRequest.objects.all().order_by('-created_at')
    serializer_class = ProjectistRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        req = self.get_object()
        req.status = 'approved'
        req.decided_at = timezone.now()
        req.decided_by = request.user
        req.save()
        # Adicionar role de projetista
        role, _ = Role.objects.get_or_create(code='projetista', defaults={'name': 'Projetista'})
        req.user.roles.add(role)
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        req = self.get_object()
        req.status = 'rejected'
        req.decided_at = timezone.now()
        req.decided_by = request.user
        req.save()
        return Response({'status': 'rejected'})


# =============================================================================
# GESTÃO
# =============================================================================

class AcessoGestaoViewSet(viewsets.ModelViewSet):
    queryset = AcessoGestao.objects.all()
    serializer_class = AcessoGestaoSerializer
    permission_classes = [IsSuperUser]

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        acesso = self.get_object()
        acesso.tem_acesso = not acesso.tem_acesso
        acesso.concedido_por = request.user
        acesso.save()
        return Response(AcessoGestaoSerializer(acesso).data)


class ConfiguracaoViewSet(viewsets.ModelViewSet):
    queryset = Configuracao.objects.all()
    serializer_class = ConfiguracaoSerializer
    permission_classes = [IsGestaoAuthorized]
    filterset_fields = ['categoria']


# =============================================================================
# OPTIONS
# =============================================================================

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['nome_do_material', 'marca']
    filterset_fields = ['situacao']


class MembroViewSet(viewsets.ModelViewSet):
    queryset = Membro.objects.all()
    serializer_class = MembroSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['nome', 'cargo']
    filterset_fields = ['ativo']


class CategoriaServicoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaServico.objects.all()
    serializer_class = CategoriaServicoSerializer
    permission_classes = [IsStaffOrReadOnly]


class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.all().select_related('categoria')
    serializer_class = ServicoSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['nome', 'descricao_curta']
    filterset_fields = ['categoria', 'disponivel']


class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['nome']


class SolicitacaoInteresseViewSet(viewsets.ModelViewSet):
    queryset = SolicitacaoInteresse.objects.all().order_by('-data_solicitacao')
    serializer_class = SolicitacaoInteresseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'servico']

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return [IsAuthenticated()]


class NoticiaViewSet(viewsets.ModelViewSet):
    queryset = Noticia.objects.all().prefetch_related('hashtags').order_by('-data_publicacao')
    serializer_class = NoticiaSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['titulo', 'resumo']
    filterset_fields = ['destaque', 'publicado']
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


# =============================================================================
# INVENTÁRIO
# =============================================================================

class CategoriaInventarioViewSet(viewsets.ModelViewSet):
    queryset = CategoriaInventario.objects.all()
    serializer_class = CategoriaInventarioSerializer
    permission_classes = [IsAdminUser]
    search_fields = ['nome']


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().select_related('categoria')
    serializer_class = ItemSerializer
    permission_classes = [IsAdminUser]
    search_fields = ['nome', 'codigo', 'descricao']
    filterset_fields = ['categoria', 'unidade']
    ordering_fields = ['nome', 'quantidade', 'data_cadastro']

    @action(detail=False)
    def criticos(self, request):
        """Retorna itens com estoque baixo."""
        itens = [item for item in self.get_queryset() if item.estoque_baixo]
        serializer = self.get_serializer(itens, many=True)
        return Response(serializer.data)


class EmprestimoViewSet(viewsets.ModelViewSet):
    queryset = Emprestimo.objects.all().select_related('item', 'usuario')
    serializer_class = EmprestimoSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['item', 'usuario']
    ordering_fields = ['data_emprestimo']

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        """Registra a devolução de um empréstimo."""
        emprestimo = self.get_object()
        if emprestimo.data_devolucao:
            return Response(
                {'error': 'Este empréstimo já foi devolvido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emprestimo.data_devolucao = timezone.now()
        emprestimo.responsavel_devolucao = request.user
        emprestimo.save()
        return Response(EmprestimoSerializer(emprestimo).data)


# =============================================================================
# PROJETOS
# =============================================================================

class ProjetoTagViewSet(viewsets.ModelViewSet):
    queryset = ProjetoTag.objects.all()
    serializer_class = ProjetoTagSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['nome']


class ProjetoViewSet(viewsets.ModelViewSet):
    queryset = Projeto.objects.all().select_related('responsavel').prefetch_related('tags', 'participantes')
    serializer_class = ProjetoSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['titulo', 'descricao']
    filterset_fields = ['status', 'publicado', 'destaque']
    lookup_field = 'slug'
    ordering_fields = ['data_criacao', 'titulo']

    def get_queryset(self):
        qs = self.queryset
        if not self.request.user.is_staff:
            qs = qs.filter(publicado=True)
        return qs


class ComentarioProjetoViewSet(viewsets.ModelViewSet):
    queryset = ComentarioProjeto.objects.all().select_related('autor', 'projeto')
    serializer_class = ComentarioProjetoSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filterset_fields = ['projeto']

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)


class ProjetoGrupoViewSet(viewsets.ModelViewSet):
    queryset = ProjetoGrupo.objects.all().prefetch_related('projetos', 'membros')
    serializer_class = ProjetoGrupoSerializer
    permission_classes = [IsSuperUser]
    search_fields = ['nome']


class TodoTaskViewSet(viewsets.ModelViewSet):
    queryset = TodoTask.objects.all()
    serializer_class = TodoTaskSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['prioridade', 'concluida', 'projeto']
    search_fields = ['titulo']
    ordering_fields = ['data_limite', 'prioridade']

    def get_queryset(self):
        qs = self.queryset
        if not self.request.user.is_staff:
            qs = qs.filter(usuario=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


# =============================================================================
# LOGS
# =============================================================================

class ActionViewSet(viewsets.ReadOnlyModelViewSet):
    """Logs são somente leitura via API."""
    queryset = Action.objects.all().order_by('-date', '-time')
    serializer_class = ActionSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['severity', 'type']
    search_fields = ['description', 'author']
    ordering_fields = ['date', 'severity']


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().select_related('created_by').prefetch_related('participants')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['event_type', 'approved']
    search_fields = ['title']
    ordering_fields = ['start_time']

    def get_queryset(self):
        qs = self.queryset
        if not self.request.user.is_staff:
            qs = qs.filter(
                Q(approved=True) | Q(created_by=self.request.user)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        event = self.get_object()
        event.approved = True
        event.save()
        return Response(EventSerializer(event).data)

    @action(detail=False, permission_classes=[IsAdminUser])
    def pending(self, request):
        """Lista eventos pendentes de aprovação."""
        pending = self.get_queryset().filter(approved=False)
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)


class LabScheduleViewSet(viewsets.ModelViewSet):
    queryset = LabSchedule.objects.all()
    serializer_class = LabScheduleSerializer
    permission_classes = [IsStaffOrReadOnly]


# =============================================================================
# CONTROLE AR
# =============================================================================

class CarouselImageViewSet(viewsets.ModelViewSet):
    queryset = CarouselImage.objects.filter(active=True)
    serializer_class = CarouselImageSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class ArCondicionadoViewSet(viewsets.ModelViewSet):
    queryset = Ar_condicionado.objects.all()
    serializer_class = ArCondicionadoSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Liga/desliga o ar condicionado."""
        ar = self.get_object()
        ar.estado = not ar.estado
        ar.save()
        # Criar comando pendente
        Comando_ar.objects.create(
            ar_condicionado=ar,
            comando='ligar' if ar.estado else 'desligar',
        )
        # Registrar log
        LogOperacao.objects.create(
            ar_condicionado=ar,
            operacao='ligar' if ar.estado else 'desligar',
            usuario=str(request.user),
        )
        return Response(ArCondicionadoSerializer(ar).data)

    @action(detail=True, methods=['post'])
    def set_temperature(self, request, pk=None):
        """Altera a temperatura do ar condicionado."""
        ar = self.get_object()
        temp = request.data.get('temperatura')
        if temp is not None:
            ar.temperatura = int(temp)
            ar.save()
            Comando_ar.objects.create(
                ar_condicionado=ar,
                comando=f'temperatura:{temp}',
            )
            LogOperacao.objects.create(
                ar_condicionado=ar,
                operacao=f'Temperatura alterada para {temp}°C',
                usuario=str(request.user),
            )
        return Response(ArCondicionadoSerializer(ar).data)


class ComandoArViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comando_ar.objects.all().order_by('-data_hora')
    serializer_class = ComandoArSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['executado', 'ar_condicionado']


# =============================================================================
# CANVA (KANBAN)
# =============================================================================

class KanbanColumnViewSet(viewsets.ModelViewSet):
    queryset = KanbanColumn.objects.all()
    serializer_class = KanbanColumnSerializer
    permission_classes = [IsAuthenticated]


class KanbanCardViewSet(viewsets.ModelViewSet):
    queryset = KanbanCard.objects.all().select_related('coluna', 'projeto', 'responsavel')
    serializer_class = KanbanCardSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['coluna', 'projeto', 'responsavel', 'prioridade', 'visivel']
    search_fields = ['titulo', 'descricao']
    ordering_fields = ['ordem', 'prazo', 'prioridade']

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move um card para outra coluna e/ou posição."""
        card = self.get_object()
        coluna_id = request.data.get('coluna')
        ordem = request.data.get('ordem')
        if coluna_id:
            card.coluna_id = coluna_id
        if ordem is not None:
            card.ordem = ordem
        card.save()
        return Response(KanbanCardSerializer(card).data)


# =============================================================================
# REPOSITÓRIO
# =============================================================================

class ResourceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['name']


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all().select_related('category', 'uploaded_by').prefetch_related('resource_files')
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['title', 'description']
    filterset_fields = ['category', 'resource_type', 'visibility']
    lookup_field = 'slug'


class ResourceFileViewSet(viewsets.ModelViewSet):
    queryset = ResourceFile.objects.all()
    serializer_class = ResourceFileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['resource']


class ResourceCommentViewSet(viewsets.ModelViewSet):
    queryset = ResourceComment.objects.all().select_related('user')
    serializer_class = ResourceCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['resource']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# =============================================================================
# ACESSO E PONTO
# =============================================================================

class WeeklyRequiredHoursViewSet(viewsets.ModelViewSet):
    queryset = WeeklyRequiredHours.objects.all().select_related('user')
    serializer_class = WeeklyRequiredHoursSerializer
    permission_classes = [IsAdminUser]


class TimeLogViewSet(viewsets.ModelViewSet):
    queryset = TimeLog.objects.all().select_related('user')
    serializer_class = TimeLogSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'status']
    ordering_fields = ['timestamp']


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all().select_related('user')
    serializer_class = SessionSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'is_active']
    ordering_fields = ['entry_time']

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Fecha uma sessão ativa."""
        session = self.get_object()
        if session.close_session():
            return Response(SessionSerializer(session).data)
        return Response(
            {'error': 'Sessão já está fechada.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
