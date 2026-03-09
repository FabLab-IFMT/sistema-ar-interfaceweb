from rest_framework import serializers
from django.contrib.auth import get_user_model

# --- Users ---
from users.models import Role, CustomUser, Card, RegistrationRequest, ProjectistRequest

# --- Gestão ---
from gestao.models import AcessoGestao, Configuracao

# --- Options ---
from options.models import (
    Material, Membro, CategoriaServico, Servico, ProjetoExemplo,
    SolicitacaoInteresse, Hashtag, Noticia,
)

# --- Inventário ---
from inventario.models import Categoria as CategoriaInventario, Item, Emprestimo

# --- Projetos ---
from projetos.models import (
    ProjetoTag, Projeto, ProjetoImagem, ComentarioProjeto,
    ProjetoGrupo, TodoTask,
)

# --- Logs ---
from logs.models import Action, Event, LabSchedule

# --- Controle AR ---
from Controle_ar.models import CarouselImage, Ar_condicionado, Comando_ar, LogOperacao

# --- Canva (Kanban) ---
from canva.models import KanbanColumn, KanbanCard

# --- Repositório ---
from repositorio.models import ResourceCategory, Resource, ResourceFile, ResourceComment

# --- Acesso e Ponto ---
from acesso_e_ponto.models import WeeklyRequiredHours, TimeLog, Session

User = get_user_model()


# =============================================================================
# USERS
# =============================================================================

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'full_name',
            'profile_image', 'is_staff', 'is_superuser', 'is_active',
            'email_verified', 'roles', 'date_joined',
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para o endpoint /api/me/ — perfil do usuário autenticado."""
    roles = RoleSerializer(many=True, read_only=True)
    role_codes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'profile_image', 'is_staff', 'is_superuser',
            'email_verified', 'roles', 'role_codes', 'date_joined',
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined', 'email_verified']

    def get_role_codes(self, obj):
        return list(obj.role_codes())


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'


class RegistrationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationRequest
        fields = ['id', 'first_name', 'last_name', 'email', 'id_number', 'status', 'created_at']
        read_only_fields = ['created_at']


class ProjectistRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectistRequest
        fields = [
            'id', 'user', 'user_name', 'motivation', 'status',
            'created_at', 'decided_at', 'decided_by',
        ]
        read_only_fields = ['created_at', 'decided_at', 'decided_by']

    def get_user_name(self, obj):
        return str(obj.user)


# =============================================================================
# GESTÃO
# =============================================================================

class AcessoGestaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = AcessoGestao
        fields = '__all__'
        read_only_fields = ['data_concessao', 'ultima_modificacao']

    def get_usuario_nome(self, obj):
        return str(obj.usuario)


class ConfiguracaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuracao
        fields = '__all__'
        read_only_fields = ['data_atualizacao']


# =============================================================================
# OPTIONS
# =============================================================================

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class MembroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membro
        fields = '__all__'


class CategoriaServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaServico
        fields = '__all__'


class ServicoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    como_utilizar_list = serializers.SerializerMethodField()
    aplicacoes_list = serializers.SerializerMethodField()

    class Meta:
        model = Servico
        fields = '__all__'

    def get_como_utilizar_list(self, obj):
        return obj.get_como_utilizar_list()

    def get_aplicacoes_list(self, obj):
        return obj.get_aplicacoes_list()


class ProjetoExemploSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjetoExemplo
        fields = '__all__'


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = '__all__'
        read_only_fields = ['slug']


class SolicitacaoInteresseSerializer(serializers.ModelSerializer):
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)

    class Meta:
        model = SolicitacaoInteresse
        fields = '__all__'
        read_only_fields = ['data_solicitacao']


class NoticiaSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=True)
    autor_nome = serializers.SerializerMethodField()

    class Meta:
        model = Noticia
        fields = '__all__'
        read_only_fields = ['slug']

    def get_autor_nome(self, obj):
        if obj.autor:
            return str(obj.autor)
        return None


# =============================================================================
# INVENTÁRIO
# =============================================================================

class CategoriaInventarioSerializer(serializers.ModelSerializer):
    itens_count = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaInventario
        fields = '__all__'

    def get_itens_count(self, obj):
        return obj.itens.count()


class ItemSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    valor_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    estoque_baixo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['data_cadastro', 'data_atualizacao']


class EmprestimoSerializer(serializers.ModelSerializer):
    item_nome = serializers.CharField(source='item.nome', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Emprestimo
        fields = '__all__'

    def get_usuario_nome(self, obj):
        return obj.usuario.get_full_name()


# =============================================================================
# PROJETOS
# =============================================================================

class ProjetoTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjetoTag
        fields = '__all__'
        read_only_fields = ['slug']


class ProjetoImagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjetoImagem
        fields = '__all__'


class ProjetoSerializer(serializers.ModelSerializer):
    tags = ProjetoTagSerializer(many=True, read_only=True)
    imagens_adicionais = ProjetoImagemSerializer(many=True, read_only=True)
    responsavel_nome = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = '__all__'
        read_only_fields = ['slug', 'data_criacao', 'data_atualizacao']

    def get_responsavel_nome(self, obj):
        if obj.responsavel:
            return str(obj.responsavel)
        return None


class ComentarioProjetoSerializer(serializers.ModelSerializer):
    autor_nome = serializers.SerializerMethodField()

    class Meta:
        model = ComentarioProjeto
        fields = '__all__'
        read_only_fields = ['data_criacao', 'data_atualizacao']

    def get_autor_nome(self, obj):
        return str(obj.autor)


class ProjetoGrupoSerializer(serializers.ModelSerializer):
    projetos_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjetoGrupo
        fields = '__all__'
        read_only_fields = ['data_criacao', 'data_atualizacao']

    def get_projetos_count(self, obj):
        return obj.projetos.count()


class TodoTaskSerializer(serializers.ModelSerializer):
    esta_atrasada = serializers.BooleanField(read_only=True)
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = TodoTask
        fields = '__all__'

    def get_dias_restantes(self, obj):
        return obj.dias_restantes()


# =============================================================================
# LOGS
# =============================================================================

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    created_by_nome = serializers.SerializerMethodField()
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = Event
        fields = '__all__'

    def get_created_by_nome(self, obj):
        if obj.created_by:
            return str(obj.created_by)
        return None


class LabScheduleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = LabSchedule
        fields = '__all__'


# =============================================================================
# CONTROLE AR
# =============================================================================

class CarouselImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselImage
        fields = '__all__'


class ArCondicionadoSerializer(serializers.ModelSerializer):
    modo_display = serializers.CharField(read_only=True)
    velocidade_display = serializers.CharField(read_only=True)

    class Meta:
        model = Ar_condicionado
        fields = '__all__'
        read_only_fields = ['ultima_alteracao']


class ComandoArSerializer(serializers.ModelSerializer):
    ar_nome = serializers.CharField(source='ar_condicionado.nome', read_only=True)

    class Meta:
        model = Comando_ar
        fields = '__all__'
        read_only_fields = ['data_hora']


class LogOperacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogOperacao
        fields = '__all__'
        read_only_fields = ['data_hora']


# =============================================================================
# CANVA (KANBAN)
# =============================================================================

class KanbanColumnSerializer(serializers.ModelSerializer):
    cards_count = serializers.SerializerMethodField()

    class Meta:
        model = KanbanColumn
        fields = '__all__'

    def get_cards_count(self, obj):
        return obj.cards.count()


class KanbanCardSerializer(serializers.ModelSerializer):
    coluna_nome = serializers.CharField(source='coluna.nome', read_only=True)
    responsavel_nome = serializers.SerializerMethodField()

    class Meta:
        model = KanbanCard
        fields = '__all__'
        read_only_fields = ['data_criacao', 'data_atualizacao']

    def get_responsavel_nome(self, obj):
        if obj.responsavel:
            return str(obj.responsavel)
        return None


# =============================================================================
# REPOSITÓRIO
# =============================================================================

class ResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = '__all__'
        read_only_fields = ['slug']


class ResourceFileSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(read_only=True)
    file_extension = serializers.CharField(read_only=True)

    class Meta:
        model = ResourceFile
        fields = '__all__'
        read_only_fields = ['upload_date']


class ResourceSerializer(serializers.ModelSerializer):
    resource_files = ResourceFileSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Resource
        fields = '__all__'
        read_only_fields = ['slug', 'created_at', 'updated_at']


class ResourceCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ResourceComment
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_user_name(self, obj):
        return str(obj.user)


# =============================================================================
# ACESSO E PONTO
# =============================================================================

class WeeklyRequiredHoursSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyRequiredHours
        fields = '__all__'
        read_only_fields = ['last_modified']

    def get_user_name(self, obj):
        return str(obj.user)


class TimeLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TimeLog
        fields = '__all__'
        read_only_fields = ['timestamp']

    def get_user_name(self, obj):
        return str(obj.user)


class SessionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = '__all__'

    def get_user_name(self, obj):
        return str(obj.user)

    def get_duration_display(self, obj):
        duration = obj.calculate_duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}h {minutes}min"
        return None
