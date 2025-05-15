from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import AcessoGestao, ConfiguracaoSistema
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
# Para estatísticas do sistema
from logs.models import Action
from projetos.models import Projeto
from options.models import Noticia

# Obtém o modelo de usuário configurado no projeto
User = get_user_model()

# Verificação para acesso à área de gestão
def is_gestao_authorized(user):
    """Verifica se o usuário tem permissão para acessar a área de gestão"""
    if user.is_superuser:
        return True
    try:
        return user.acesso_gestao.tem_acesso
    except:
        return False

@login_required
@user_passes_test(is_gestao_authorized)
def dashboard_gestao(request):
    """Dashboard principal da área de gestão"""
    context = {
        'titulo': 'Dashboard de Gestão',
    }
    return render(request, 'gestao/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gerenciar_acessos(request):
    """Gerenciamento de acessos à área de gestão (apenas superusuários)"""
    
    # Busca todos os usuários staff que não são superusuários
    users = User.objects.filter(is_staff=True).exclude(is_superuser=True)
    
    # Busca termo de pesquisa
    termo_busca = request.GET.get('search', '')
    if termo_busca:
        users = users.filter(
            Q(username__icontains=termo_busca) |
            Q(first_name__icontains=termo_busca) |
            Q(last_name__icontains=termo_busca) |
            Q(email__icontains=termo_busca)
        )
    
    # Para cada usuário, verificar se já tem acesso ou criar um novo registro
    for user in users:
        AcessoGestao.objects.get_or_create(usuario=user, defaults={'tem_acesso': False, 'concedido_por': request.user})
    
    context = {
        'titulo': 'Gerenciar Acessos',
        'users': users,
        'termo_busca': termo_busca,
    }
    return render(request, 'gestao/gerenciar_acessos.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_acesso(request, user_id):
    """Alterna o acesso de um usuário à área de gestão"""
    
    usuario = get_object_or_404(User, id=user_id)
    if usuario.is_superuser:
        messages.error(request, "Não é possível modificar o acesso de um superusuário.")
        return redirect('gestao:gerenciar_acessos')
    
    acesso, created = AcessoGestao.objects.get_or_create(
        usuario=usuario,
        defaults={'tem_acesso': False, 'concedido_por': request.user}
    )
    
    # Alterna o estado atual
    acesso.tem_acesso = not acesso.tem_acesso
    acesso.concedido_por = request.user
    acesso.save()
    
    status = "concedido" if acesso.tem_acesso else "revogado"
    messages.success(request, f"Acesso à gestão {status} para {usuario.username}.")
    
    return redirect('gestao:gerenciar_acessos')

@login_required
@user_passes_test(is_gestao_authorized)
def monitoramento_sistema(request):
    """Monitoramento do sistema com estatísticas e métricas"""
    
    # Obter estatísticas gerais
    total_usuarios = User.objects.count()
    usuarios_ativos = User.objects.filter(is_active=True).count()
    usuarios_staff = User.objects.filter(is_staff=True).count()
    usuarios_superuser = User.objects.filter(is_superuser=True).count()
    
    # Atividade recente (última semana)
    data_inicio = timezone.now() - timedelta(days=7)
    # Adaptando para usar o modelo Action em vez de LogActivity
    logs_recentes = Action.objects.filter(date__gte=data_inicio.date()).order_by('-date', '-time')[:10]
    
    # Contagem de atividades por dia na última semana
    logs_por_dia = Action.objects.filter(
        date__gte=data_inicio.date()
    ).values('date').annotate(
        contagem=Count('id')
    ).order_by('date')
    
    # Estatísticas de projetos
    total_projetos = Projeto.objects.count()
    try:
        projetos_ativos = Projeto.objects.filter(status='Ativo').count()
        projetos_concluidos = Projeto.objects.filter(status='Concluído').count()
    except:
        # Em caso de erro no campo status, use valores padrão
        projetos_ativos = 0
        projetos_concluidos = 0
    
    # Notícias recentes
    noticias_recentes = Noticia.objects.order_by('-data_publicacao')[:5]
    
    # Usuários mais ativos (baseado em logs de Action, adaptado)
    usuarios_mais_ativos = []
    # Como Action pode não ter uma relação direta com usuários, esta funcionalidade
    # será simplificada ou omitida nesta versão
    
    context = {
        'titulo': 'Monitoramento do Sistema',
        'total_usuarios': total_usuarios,
        'usuarios_ativos': usuarios_ativos,
        'usuarios_staff': usuarios_staff,
        'usuarios_superuser': usuarios_superuser,
        'logs_recentes': logs_recentes,
        'logs_por_dia': logs_por_dia,
        'total_projetos': total_projetos,
        'projetos_ativos': projetos_ativos,
        'projetos_concluidos': projetos_concluidos,
        'noticias_recentes': noticias_recentes,
        'usuarios_mais_ativos': usuarios_mais_ativos,
        'periodo': '7 dias',
    }
    
    return render(request, 'gestao/monitoramento.html', context)

@login_required
@user_passes_test(is_gestao_authorized)
def configuracoes_sistema(request):
    """View para gerenciar as configurações do sistema"""
    
    # Separar configurações por categoria
    categorias = {}
    for categoria_code, categoria_nome in ConfiguracaoSistema.CATEGORIA_CHOICES:
        # Filtrar configurações que apenas superusuários podem ver/editar
        if not request.user.is_superuser:
            configs = ConfiguracaoSistema.objects.filter(categoria=categoria_code, restrito=False)
        else:
            configs = ConfiguracaoSistema.objects.filter(categoria=categoria_code)
            
        if configs.exists():
            categorias[categoria_code] = {
                'nome': categoria_nome,
                'configs': configs
            }
    
    # Se há POST, estamos salvando configurações
    if request.method == 'POST':
        # Verificação de permissão adicional
        if 'config_id' in request.POST and 'valor' in request.POST:
            config_id = request.POST.get('config_id')
            valor = request.POST.get('valor')
            
            try:
                config = ConfiguracaoSistema.objects.get(id=config_id)
                
                # Verificar se o usuário tem permissão para editar esta configuração
                if config.restrito and not request.user.is_superuser:
                    messages.error(request, "Você não tem permissão para alterar esta configuração.")
                    return redirect('gestao:configuracoes')
                
                # Validação básica de tipo
                if config.tipo == 'numero':
                    try:
                        float(valor)  # Apenas verifica se é um número válido
                    except ValueError:
                        messages.error(request, f"O valor para {config.nome} deve ser um número.")
                        return redirect('gestao:configuracoes')
                
                # Salvar a configuração
                config.valor = valor
                config.modificado_por = request.user
                config.save()
                
                messages.success(request, f"Configuração '{config.nome}' atualizada com sucesso.")
                
            except ConfiguracaoSistema.DoesNotExist:
                messages.error(request, "Configuração não encontrada.")
        
        return redirect('gestao:configuracoes')
    
    context = {
        'titulo': 'Configurações do Sistema',
        'categorias': categorias
    }
    
    return render(request, 'gestao/configuracoes.html', context)
