from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import AcessoGestao, Configuracao
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Imports de modelos dos outros apps
from logs.models import Action
from projetos.models import Projeto
from options.models import Noticia, NoticiaFoto, Membro, Servico, SolicitacaoInteresse, Material
from inventario.models import Item, Categoria, Emprestimo
from users.models import Role, ProjectistRequest

User = get_user_model()


# ─────────────────────────────────────────────
# Helpers de permissão
# ─────────────────────────────────────────────

def is_gestao_authorized(user):
    """
    Verifica se o usuário tem permissão para acessar a área de gestão.
    Qualquer is_staff (inclusive quem tem cargo com is_staff_equivalent=True)
    pode entrar no painel — o que cada um VÊ é filtrado pelos admin_sections.
    """
    if user.is_superuser or user.is_staff:
        return True
    try:
        return user.acesso_gestao.tem_acesso
    except Exception:
        return False


def is_staff_or_gestao(user):
    """Staff ou autorizado pela gestão."""
    return user.is_staff or is_gestao_authorized(user)


# ─────────────────────────────────────────────
# Dashboard principal
# ─────────────────────────────────────────────

@login_required
@user_passes_test(is_gestao_authorized)
def dashboard_gestao(request):
    """Dashboard principal da área de gestão com estatísticas reais."""

    # Estatísticas gerais
    total_usuarios = User.objects.count()
    usuarios_ativos = User.objects.filter(is_active=True).count()
    usuarios_staff = User.objects.filter(is_staff=True).count()

    # Projetos — usa os choices reais do modelo
    total_projetos = Projeto.objects.count()
    projetos_ativos = Projeto.objects.filter(status='em_andamento').count()
    projetos_concluidos = Projeto.objects.filter(status='concluido').count()

    # Inventário
    total_itens = Item.objects.count()
    itens_estoque_baixo = sum(1 for i in Item.objects.all() if i.estoque_baixo)
    emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).count()

    # Logs recentes (últimos 7 dias)
    data_inicio = timezone.now() - timedelta(days=7)
    logs_recentes = Action.objects.filter(
        date__gte=data_inicio.date()
    ).order_by('-date', '-time')[:8]
    total_logs_semana = Action.objects.filter(date__gte=data_inicio.date()).count()

    # Solicitações pendentes
    solicitacoes_pendentes = SolicitacaoInteresse.objects.filter(status='pendente').count()
    projectist_pendentes = ProjectistRequest.objects.filter(status='pending').count()

    # Notícias recentes
    noticias_recentes = Noticia.objects.order_by('-data_publicacao')[:5]

    context = {
        'titulo': 'Dashboard de Gestão',
        'total_usuarios': total_usuarios,
        'usuarios_ativos': usuarios_ativos,
        'usuarios_staff': usuarios_staff,
        'total_projetos': total_projetos,
        'projetos_ativos': projetos_ativos,
        'projetos_concluidos': projetos_concluidos,
        'total_itens': total_itens,
        'itens_estoque_baixo': itens_estoque_baixo,
        'emprestimos_ativos': emprestimos_ativos,
        'logs_recentes': logs_recentes,
        'total_logs_semana': total_logs_semana,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'projectist_pendentes': projectist_pendentes,
        'noticias_recentes': noticias_recentes,
    }
    return render(request, 'gestao/dashboard.html', context)


# ─────────────────────────────────────────────
# Monitoramento do sistema
# ─────────────────────────────────────────────

@login_required
@user_passes_test(is_gestao_authorized)
def monitoramento_sistema(request):
    """Monitoramento do sistema com estatísticas e métricas."""

    total_usuarios = User.objects.count()
    usuarios_ativos = User.objects.filter(is_active=True).count()
    usuarios_staff = User.objects.filter(is_staff=True).count()
    usuarios_superuser = User.objects.filter(is_superuser=True).count()

    data_inicio = timezone.now() - timedelta(days=7)
    logs_recentes = Action.objects.filter(
        date__gte=data_inicio.date()
    ).order_by('-date', '-time')[:10]

    logs_por_dia = Action.objects.filter(
        date__gte=data_inicio.date()
    ).values('date').annotate(contagem=Count('id')).order_by('date')

    # Status corretos do modelo Projeto
    total_projetos = Projeto.objects.count()
    projetos_ativos = Projeto.objects.filter(status='em_andamento').count()
    projetos_concluidos = Projeto.objects.filter(status='concluido').count()

    # Notícias — usa o campo correto 'publicado'
    noticias_recentes = Noticia.objects.order_by('-data_publicacao')[:5]

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
        'usuarios_mais_ativos': [],
        'periodo': '7 dias',
    }
    return render(request, 'gestao/monitoramento.html', context)


# ─────────────────────────────────────────────
# Gerenciar acessos à gestão
# ─────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gerenciar_acessos(request):
    """Gerenciamento de acessos à área de gestão (apenas superusuários)."""

    # BUG FIX: buscava por 'username' que não existe no modelo customizado.
    # Agora busca por id (matrícula), first_name, last_name ou email.
    users = User.objects.filter(is_staff=True).exclude(is_superuser=True)

    termo_busca = request.GET.get('search', '')
    if termo_busca:
        users = users.filter(
            Q(id__icontains=termo_busca) |
            Q(first_name__icontains=termo_busca) |
            Q(last_name__icontains=termo_busca) |
            Q(email__icontains=termo_busca)
        )

    for user in users:
        AcessoGestao.objects.get_or_create(
            usuario=user,
            defaults={'tem_acesso': False, 'concedido_por': request.user}
        )

    context = {
        'titulo': 'Gerenciar Acessos à Gestão',
        'users': users,
        'termo_busca': termo_busca,
    }
    return render(request, 'gestao/gerenciar_acessos.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def toggle_acesso(request, user_id):
    """Alterna o acesso de um usuário à área de gestão."""
    usuario = get_object_or_404(User, id=user_id)
    if usuario.is_superuser:
        messages.error(request, "Não é possível modificar o acesso de um superusuário.")
        return redirect('gestao:gerenciar_acessos')

    acesso, _ = AcessoGestao.objects.get_or_create(
        usuario=usuario,
        defaults={'tem_acesso': False, 'concedido_por': request.user}
    )
    acesso.tem_acesso = not acesso.tem_acesso
    acesso.concedido_por = request.user
    acesso.save()

    status = "concedido" if acesso.tem_acesso else "revogado"
    messages.success(
        request,
        f"Acesso à gestão {status} para {usuario.first_name} {usuario.last_name}."
    )
    return redirect('gestao:gerenciar_acessos')


# ─────────────────────────────────────────────
# Admin — Usuários
# ─────────────────────────────────────────────

@login_required
@user_passes_test(is_gestao_authorized)
def admin_usuarios(request):
    """Lista e gerencia todos os usuários do sistema."""
    users = User.objects.all().prefetch_related('roles').order_by('first_name', 'last_name')

    termo = request.GET.get('q', '')
    filtro_status = request.GET.get('status', '')
    filtro_role = request.GET.get('role', '')

    if termo:
        users = users.filter(
            Q(id__icontains=termo) |
            Q(first_name__icontains=termo) |
            Q(last_name__icontains=termo) |
            Q(email__icontains=termo)
        )
    if filtro_status == 'ativo':
        users = users.filter(is_active=True)
    elif filtro_status == 'inativo':
        users = users.filter(is_active=False)
    elif filtro_status == 'staff':
        users = users.filter(is_staff=True)
    elif filtro_status == 'superuser':
        users = users.filter(is_superuser=True)

    if filtro_role:
        users = users.filter(roles__code=filtro_role)

    roles = Role.objects.all().order_by('name')
    projectist_pendentes = ProjectistRequest.objects.filter(status='pending').select_related('user')

    context = {
        'titulo': 'Gerenciar Usuários',
        'users': users,
        'roles': roles,
        'termo': termo,
        'filtro_status': filtro_status,
        'filtro_role': filtro_role,
        'total': users.count(),
        'projectist_pendentes': projectist_pendentes,
    }
    return render(request, 'gestao/admin_usuarios.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
def admin_usuario_editar(request, user_id):
    """Edita um usuário: roles, status ativo, staff."""
    usuario = get_object_or_404(User, id=user_id)
    roles = Role.objects.all().order_by('name')

    if request.method == 'POST':
        # Atualiza roles
        selected_codes = request.POST.getlist('roles')
        selected_roles = roles.filter(code__in=selected_codes)
        usuario.roles.set(selected_roles)

        # Atualiza flags (apenas superuser pode mudar is_staff/is_superuser)
        if request.user.is_superuser:
            usuario.is_active = 'is_active' in request.POST
            # Propaga staff via roles ou toggle manual
            has_staff_role = selected_roles.filter(is_staff_equivalent=True).exists()
            manual_staff = 'is_staff' in request.POST
            usuario.is_staff = usuario.is_superuser or has_staff_role or manual_staff

        usuario.save(update_fields=['is_active', 'is_staff'])
        messages.success(request, f"Usuário {usuario.first_name} {usuario.last_name} atualizado com sucesso.")
        return redirect('gestao:admin_usuarios')

    context = {
        'titulo': f'Editar Usuário — {usuario.first_name} {usuario.last_name}',
        'usuario': usuario,
        'roles': roles,
        'usuario_roles': set(usuario.roles.values_list('code', flat=True)),
    }
    return render(request, 'gestao/admin_usuario_editar.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def admin_usuario_toggle_ativo(request, user_id):
    """Liga/desliga status ativo de um usuário."""
    usuario = get_object_or_404(User, id=user_id)
    if usuario == request.user:
        messages.error(request, "Você não pode desativar sua própria conta.")
        return redirect('gestao:admin_usuarios')
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])
    status = "ativado" if usuario.is_active else "desativado"
    messages.success(request, f"Usuário {usuario.first_name} {status}.")
    return redirect('gestao:admin_usuarios')


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def admin_usuario_toggle_staff(request, user_id):
    """Liga/desliga status staff de um usuário."""
    usuario = get_object_or_404(User, id=user_id)
    if usuario == request.user:
        messages.error(request, "Você não pode alterar sua própria permissão de staff.")
        return redirect('gestao:admin_usuarios')
    usuario.is_staff = not usuario.is_staff
    usuario.save(update_fields=['is_staff'])
    status = "promovido a staff" if usuario.is_staff else "removido do staff"
    messages.success(request, f"Usuário {usuario.first_name} {status}.")
    return redirect('gestao:admin_usuarios')


# ─────────────────────────────────────────────
# Admin — Conteúdo (Notícias, Membros, Serviços, Solicitações)
# ─────────────────────────────────────────────

@login_required
@user_passes_test(is_gestao_authorized)
def admin_conteudo(request):
    """Visão geral da gestão de conteúdo do site."""
    total_noticias = Noticia.objects.count()
    noticias_publicadas = Noticia.objects.filter(publicado=True).count()
    total_membros = Membro.objects.count()
    membros_ativos = Membro.objects.filter(ativo=True).count()
    total_servicos = Servico.objects.count()
    servicos_disponiveis = Servico.objects.filter(disponivel=True).count()
    solicitacoes_pendentes = SolicitacaoInteresse.objects.filter(status='pendente').count()
    total_equipamentos = Material.objects.count()
    equipamentos_ativos = Material.objects.filter(situacao='ativo').count()

    context = {
        'titulo': 'Gestão de Conteúdo',
        'total_noticias': total_noticias,
        'noticias_publicadas': noticias_publicadas,
        'total_membros': total_membros,
        'membros_ativos': membros_ativos,
        'total_servicos': total_servicos,
        'servicos_disponiveis': servicos_disponiveis,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'total_equipamentos': total_equipamentos,
        'equipamentos_ativos': equipamentos_ativos,
    }
    return render(request, 'gestao/admin_conteudo.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
def admin_noticias(request):
    """Lista e gerencia notícias."""
    noticias = Noticia.objects.all().select_related('autor').prefetch_related('hashtags').order_by('-data_publicacao')

    termo = request.GET.get('q', '')
    filtro = request.GET.get('status', '')
    if termo:
        noticias = noticias.filter(Q(titulo__icontains=termo) | Q(resumo__icontains=termo))
    if filtro == 'publicado':
        noticias = noticias.filter(publicado=True)
    elif filtro == 'rascunho':
        noticias = noticias.filter(publicado=False)
    elif filtro == 'destaque':
        noticias = noticias.filter(destaque=True)
    elif filtro == 'home':
        noticias = noticias.filter(mostrar_na_home=True)

    context = {
        'titulo': 'Gerenciar Notícias',
        'noticias': noticias,
        'termo': termo,
        'filtro': filtro,
        'total': noticias.count(),
    }
    return render(request, 'gestao/admin_noticias.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def admin_noticia_toggle_publicado(request, noticia_id):
    """Publica/despublica uma notícia."""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    noticia.publicado = not noticia.publicado
    noticia.save(update_fields=['publicado'])
    status = "publicada" if noticia.publicado else "despublicada"
    messages.success(request, f"Notícia '{noticia.titulo}' {status}.")
    return redirect('gestao:admin_noticias')


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def admin_noticia_toggle_destaque(request, noticia_id):
    """Coloca/retira notícia do destaque."""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    noticia.destaque = not noticia.destaque
    noticia.save(update_fields=['destaque'])
    status = "em destaque" if noticia.destaque else "fora do destaque"
    messages.success(request, f"Notícia '{noticia.titulo}' agora está {status}.")
    return redirect('gestao:admin_noticias')


@login_required
@user_passes_test(is_gestao_authorized)
def admin_membros(request):
    """Lista e gerencia membros da equipe."""
    membros = Membro.objects.all().order_by('ordem', 'nome')

    context = {
        'titulo': 'Gerenciar Membros',
        'membros': membros,
        'total': membros.count(),
        'ativos': membros.filter(ativo=True).count(),
    }
    return render(request, 'gestao/admin_membros.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def admin_membro_toggle_ativo(request, membro_id):
    """Ativa/desativa um membro."""
    membro = get_object_or_404(Membro, id=membro_id)
    membro.ativo = not membro.ativo
    membro.save(update_fields=['ativo'])
    status = "ativado" if membro.ativo else "desativado"
    messages.success(request, f"Membro {membro.nome} {status}.")
    return redirect('gestao:admin_membros')


@login_required
@user_passes_test(is_gestao_authorized)
def admin_servicos(request):
    """Lista e gerencia serviços do lab."""
    servicos = Servico.objects.all().select_related('categoria').order_by('ordem', 'nome')

    context = {
        'titulo': 'Gerenciar Serviços',
        'servicos': servicos,
        'total': servicos.count(),
        'disponiveis': servicos.filter(disponivel=True).count(),
    }
    return render(request, 'gestao/admin_servicos.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def admin_servico_toggle_disponivel(request, servico_id):
    """Ativa/desativa disponibilidade de um serviço."""
    servico = get_object_or_404(Servico, id=servico_id)
    servico.disponivel = not servico.disponivel
    servico.save(update_fields=['disponivel'])
    status = "disponível" if servico.disponivel else "indisponível"
    messages.success(request, f"Serviço '{servico.nome}' agora está {status}.")
    return redirect('gestao:admin_servicos')


@login_required
@user_passes_test(is_gestao_authorized)
def admin_solicitacoes(request):
    """Gerencia solicitações de interesse nos serviços."""
    solicitacoes = SolicitacaoInteresse.objects.all().select_related(
        'usuario', 'servico'
    ).order_by('-data_solicitacao')

    filtro = request.GET.get('status', '')
    if filtro:
        solicitacoes = solicitacoes.filter(status=filtro)

    context = {
        'titulo': 'Solicitações de Interesse',
        'solicitacoes': solicitacoes,
        'filtro': filtro,
        'total': solicitacoes.count(),
        'status_choices': SolicitacaoInteresse.STATUS_CHOICES,
    }
    return render(request, 'gestao/admin_solicitacoes.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def admin_solicitacao_status(request, sol_id):
    """Atualiza o status de uma solicitação."""
    sol = get_object_or_404(SolicitacaoInteresse, id=sol_id)
    novo_status = request.POST.get('status')
    obs = request.POST.get('observacoes_admin', '')
    status_validos = [s[0] for s in SolicitacaoInteresse.STATUS_CHOICES]
    if novo_status in status_validos:
        sol.status = novo_status
        if obs:
            sol.observacoes_admin = obs
        sol.save(update_fields=['status', 'observacoes_admin'])
        messages.success(request, f"Status da solicitação #{sol.id} atualizado para '{sol.get_status_display()}'.")
    else:
        messages.error(request, "Status inválido.")
    return redirect('gestao:admin_solicitacoes')


# ─────────────────────────────────────────────
# Admin — Inventário (overview)
# ─────────────────────────────────────────────

@login_required
@user_passes_test(is_gestao_authorized)
def admin_inventario_overview(request):
    """Visão geral rápida do inventário na área de gestão."""
    categorias = Categoria.objects.annotate(total_itens=Count('itens')).order_by('nome')
    itens = Item.objects.select_related('categoria').order_by('nome')
    emprestimos_ativos = Emprestimo.objects.filter(
        data_devolucao__isnull=True
    ).select_related('item', 'usuario').order_by('-data_emprestimo')
    emprestimos_atrasados = [e for e in emprestimos_ativos if e.status == 'atrasado']

    itens_baixo_estoque = [i for i in itens if i.estoque_baixo]

    context = {
        'titulo': 'Inventário — Visão Geral',
        'categorias': categorias,
        'itens': itens,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_atrasados': emprestimos_atrasados,
        'itens_baixo_estoque': itens_baixo_estoque,
        'total_itens': itens.count(),
        'total_emprestimos_ativos': emprestimos_ativos.count(),
        'total_atrasados': len(emprestimos_atrasados),
        'total_baixo_estoque': len(itens_baixo_estoque),
    }
    return render(request, 'gestao/admin_inventario.html', context)


# ─────────────────────────────────────────────
# Configurações do sistema (corrigida)
# ─────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_superuser)
def configuracoes_sistema(request):
    """Gerencia configurações do sistema por categoria."""
    categorias_choices = Configuracao._meta.get_field('categoria').choices
    categoria_ativa = request.GET.get('categoria', 'geral')

    configuracoes = Configuracao.objects.filter(
        categoria=categoria_ativa
    ).order_by('nome')

    if request.method == 'POST':
        for config in Configuracao.objects.all():
            novo_valor = request.POST.get(f'config_{config.id}')
            if novo_valor is not None and novo_valor != config.valor:
                config.valor = novo_valor
                config.save(update_fields=['valor', 'data_atualizacao'])
        messages.success(request, "Configurações salvas com sucesso.")
        return redirect(f"{request.path}?categoria={categoria_ativa}")

    context = {
        'titulo': 'Configurações do Sistema',
        'configuracoes': configuracoes,
        'categorias': categorias_choices,
        'categoria_ativa': categoria_ativa,
    }
    return render(request, 'gestao/configuracoes.html', context)


# ═════════════════════════════════════════════
# CRUD — Notícias
# ═════════════════════════════════════════════

@login_required
@user_passes_test(is_gestao_authorized)
def admin_noticia_form(request, noticia_id=None):
    """Criar ou editar uma notícia, com galeria de fotos e conversão WebP automática."""
    from django.utils.text import slugify as _slugify
    from options.models import Hashtag
    from .utils import convert_to_webp

    noticia = get_object_or_404(Noticia, id=noticia_id) if noticia_id else None
    hashtags_disponiveis = Hashtag.objects.all().order_by('nome')

    if request.method == 'POST':
        titulo          = request.POST.get('titulo', '').strip()
        resumo          = request.POST.get('resumo', '').strip()
        conteudo        = request.POST.get('conteudo', '').strip()
        publicado       = 'publicado' in request.POST
        destaque        = 'destaque' in request.POST
        mostrar_na_home = 'mostrar_na_home' in request.POST
        hashtags_ids    = request.POST.getlist('hashtags')
        novas_tags_raw  = request.POST.get('novas_hashtags', '').strip()

        if not titulo:
            messages.error(request, "O título é obrigatório.")
        elif not resumo:
            messages.error(request, "O resumo é obrigatório.")
        else:
            if not noticia:
                noticia = Noticia()
                noticia.autor = request.user

            noticia.titulo          = titulo
            noticia.resumo          = resumo
            noticia.conteudo        = conteudo
            noticia.publicado       = publicado
            noticia.destaque        = destaque
            noticia.mostrar_na_home = mostrar_na_home

            # Slug único
            if not noticia.slug or noticia.titulo != titulo:
                base = _slugify(titulo)
                slug = base
                i = 1
                while Noticia.objects.filter(slug=slug).exclude(pk=noticia.pk or 0).exists():
                    slug = f"{base}-{i}"
                    i += 1
                noticia.slug = slug

            # Imagem de capa → converte para WebP automaticamente
            if 'imagem' in request.FILES:
                noticia.imagem = convert_to_webp(request.FILES['imagem'])

            noticia.save()

            # Hashtags existentes
            tags_selecionadas = list(Hashtag.objects.filter(id__in=hashtags_ids))

            # Novas hashtags digitadas
            if novas_tags_raw:
                for tag_nome in [t.strip() for t in novas_tags_raw.split(',') if t.strip()]:
                    tag_slug = _slugify(tag_nome)
                    tag_obj, _ = Hashtag.objects.get_or_create(
                        slug=tag_slug, defaults={'nome': tag_nome}
                    )
                    tags_selecionadas.append(tag_obj)

            noticia.hashtags.set(tags_selecionadas)

            # ── Fotos da galeria: exclusão ──
            fotos_deletar = request.POST.getlist('fotos_deletar')
            if fotos_deletar:
                NoticiaFoto.objects.filter(
                    id__in=fotos_deletar, noticia=noticia
                ).delete()

            # ── Fotos da galeria: novas uploads ──
            legendas  = request.POST.getlist('foto_legenda')
            ordens    = request.POST.getlist('foto_ordem')
            for idx, foto_file in enumerate(request.FILES.getlist('fotos_novas')):
                legenda = legendas[idx] if idx < len(legendas) else ''
                try:
                    ordem = int(ordens[idx]) if idx < len(ordens) else 0
                except (ValueError, TypeError):
                    ordem = 0
                NoticiaFoto.objects.create(
                    noticia=noticia,
                    imagem=convert_to_webp(foto_file),
                    legenda=legenda.strip(),
                    ordem=ordem,
                )

            action = "atualizada" if noticia_id else "criada"
            messages.success(request, f"Notícia '{noticia.titulo}' {action} com sucesso.")
            return redirect('gestao:admin_noticias')

    context = {
        'noticia': noticia,
        'fotos_galeria': noticia.fotos.all() if noticia else [],
        'hashtags_disponiveis': hashtags_disponiveis,
        'hashtags_selecionadas': set(noticia.hashtags.values_list('id', flat=True)) if noticia else set(),
        'titulo': 'Editar Notícia' if noticia else 'Nova Notícia',
    }
    return render(request, 'gestao/admin_noticia_form.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def admin_noticia_foto_deletar(request, foto_id):
    """Exclui uma foto individual da galeria de uma notícia (via AJAX ou form)."""
    foto = get_object_or_404(NoticiaFoto, id=foto_id)
    noticia_id = foto.noticia_id
    foto.delete()
    # Se for AJAX retorna JSON, senão redireciona de volta ao formulário
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('gestao:admin_noticia_editar', noticia_id=noticia_id)


@login_required
@user_passes_test(is_gestao_authorized)
def admin_noticia_deletar(request, noticia_id):
    """Excluir uma notícia com confirmação."""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    if request.method == 'POST':
        titulo = noticia.titulo
        noticia.delete()
        messages.success(request, f"Notícia '{titulo}' excluída.")
        return redirect('gestao:admin_noticias')
    return render(request, 'gestao/admin_noticia_confirmar_exclusao.html', {'noticia': noticia})


# ═════════════════════════════════════════════
# CRUD — Membros
# ═════════════════════════════════════════════

@login_required
@user_passes_test(is_gestao_authorized)
def admin_membro_form(request, membro_id=None):
    """Criar ou editar um membro da equipe."""
    from .utils import convert_to_webp
    membro = get_object_or_404(Membro, id=membro_id) if membro_id else None

    if request.method == 'POST':
        nome       = request.POST.get('nome', '').strip()
        cargo      = request.POST.get('cargo', '').strip()
        email      = request.POST.get('email', '').strip()
        bio        = request.POST.get('bio', '').strip()
        linkedin   = request.POST.get('linkedin', '').strip()
        github     = request.POST.get('github', '').strip()
        lattes     = request.POST.get('lattes', '').strip()
        ativo      = 'ativo' in request.POST
        ordem      = request.POST.get('ordem', '0') or '0'

        if not nome:
            messages.error(request, "O nome é obrigatório.")
        elif not cargo:
            messages.error(request, "O cargo é obrigatório.")
        else:
            if not membro:
                membro = Membro()

            membro.nome     = nome
            membro.cargo    = cargo
            membro.email    = email
            membro.bio      = bio
            membro.linkedin = linkedin
            membro.github   = github
            membro.lattes   = lattes
            membro.ativo    = ativo
            membro.ordem    = int(ordem)

            if 'foto' in request.FILES:
                membro.foto = convert_to_webp(request.FILES['foto'])

            membro.save()
            action = "atualizado" if membro_id else "cadastrado"
            messages.success(request, f"Membro '{membro.nome}' {action} com sucesso.")
            return redirect('gestao:admin_membros')

    context = {
        'membro': membro,
        'titulo': 'Editar Membro' if membro else 'Novo Membro',
    }
    return render(request, 'gestao/admin_membro_form.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
def admin_membro_deletar(request, membro_id):
    """Excluir um membro com confirmação."""
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        nome = membro.nome
        membro.delete()
        messages.success(request, f"Membro '{nome}' excluído.")
        return redirect('gestao:admin_membros')
    return render(request, 'gestao/admin_membro_confirmar_exclusao.html', {'membro': membro})


# ═════════════════════════════════════════════
# CRUD — Serviços
# ═════════════════════════════════════════════

@login_required
@user_passes_test(is_gestao_authorized)
def admin_servico_form(request, servico_id=None):
    """Criar ou editar um serviço."""
    from options.models import CategoriaServico
    from .utils import convert_to_webp
    servico = get_object_or_404(Servico, id=servico_id) if servico_id else None
    categorias = CategoriaServico.objects.all().order_by('ordem', 'nome')

    if request.method == 'POST':
        nome            = request.POST.get('nome', '').strip()
        descricao_curta = request.POST.get('descricao_curta', '').strip()
        descricao       = request.POST.get('descricao', '').strip()
        tempo_estimado  = request.POST.get('tempo_estimado', '').strip()
        disponivel      = 'disponivel' in request.POST
        destaque        = 'destaque' in request.POST
        ordem           = request.POST.get('ordem', '0') or '0'
        categoria_id    = request.POST.get('categoria') or None
        como_utilizar   = request.POST.get('como_utilizar', '').strip()
        aplicacoes      = request.POST.get('aplicacoes', '').strip()
        especificacoes  = request.POST.get('especificacoes', '').strip()

        if not nome:
            messages.error(request, "O nome é obrigatório.")
        elif not descricao_curta:
            messages.error(request, "A descrição curta é obrigatória.")
        elif not categoria_id:
            messages.error(request, "Selecione uma categoria.")
        else:
            if not servico:
                servico = Servico()

            from options.models import CategoriaServico
            servico.categoria       = CategoriaServico.objects.get(id=categoria_id)
            servico.nome            = nome
            servico.descricao_curta = descricao_curta
            servico.descricao       = descricao
            servico.tempo_estimado  = tempo_estimado
            servico.disponivel      = disponivel
            servico.destaque        = destaque
            servico.ordem           = int(ordem)
            servico.como_utilizar   = como_utilizar
            servico.aplicacoes      = aplicacoes
            servico.especificacoes  = especificacoes

            if 'imagem' in request.FILES:
                servico.imagem = convert_to_webp(request.FILES['imagem'])

            servico.save()
            action = "atualizado" if servico_id else "criado"
            messages.success(request, f"Serviço '{servico.nome}' {action} com sucesso.")
            return redirect('gestao:admin_servicos')

    context = {
        'servico': servico,
        'categorias': categorias,
        'titulo': 'Editar Serviço' if servico else 'Novo Serviço',
    }
    return render(request, 'gestao/admin_servico_form.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
def admin_servico_deletar(request, servico_id):
    """Excluir um serviço com confirmação."""
    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == 'POST':
        nome = servico.nome
        servico.delete()
        messages.success(request, f"Serviço '{nome}' excluído.")
        return redirect('gestao:admin_servicos')
    return render(request, 'gestao/admin_servico_confirmar_exclusao.html', {'servico': servico})
