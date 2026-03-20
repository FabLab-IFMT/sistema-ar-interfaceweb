"""
Context processors da área de gestão.
Injetam contagens de pendências e permissões de seção admin globalmente.
"""

# Mapa: code do cargo → seções admin que o usuário pode acessar
ROLE_SECTION_MAP = {
    'administrador': {
        'dashboard', 'usuarios', 'conteudo', 'noticias', 'membros',
        'servicos', 'solicitacoes', 'inventario', 'monitoramento',
        'cursos', 'projetos', 'configuracoes', 'automacao',
    },
    'gestor': {
        'dashboard', 'usuarios', 'conteudo', 'noticias', 'membros',
        'servicos', 'solicitacoes', 'inventario', 'monitoramento',
        'cursos', 'projetos', 'automacao',
    },
    'jornalista': {
        'dashboard', 'noticias',
    },
    'projetista': {
        'dashboard', 'projetos', 'cursos', 'inventario',
    },
    'secretario': {
        'dashboard', 'membros', 'servicos', 'solicitacoes',
    },
    'pesquisador': {
        'dashboard', 'projetos', 'inventario', 'monitoramento',
    },
}


def gestao_counts(request):
    """
    Injeta no contexto global:
      - solicitacoes_pendentes  : int
      - projectist_pendentes    : int
      - admin_sections          : set[str] — seções admin que o usuário atual pode ver
    """
    context = {
        'solicitacoes_pendentes': 0,
        'projectist_pendentes': 0,
        'admin_sections': set(),
    }

    if not (hasattr(request, 'user') and request.user.is_authenticated):
        return context

    user = request.user

    # ── Superuser / is_superuser vê tudo ──────────────────────────────────────
    if user.is_superuser:
        context['admin_sections'] = set(ROLE_SECTION_MAP['administrador']) | {'configuracoes'}
    elif user.is_staff:
        # Monta seções a partir dos cargos (roles) do usuário
        sections: set = set()
        try:
            for role in user.roles.all():
                sections |= ROLE_SECTION_MAP.get(role.code, set())
        except Exception:
            pass

        # Fallback: se is_staff mas sem cargos mapeados, garante ao menos dashboard
        if not sections:
            sections = {'dashboard'}

        context['admin_sections'] = sections

    # ── Contagens de pendências (apenas para quem tem acesso admin) ───────────
    if context['admin_sections']:
        try:
            from options.models import SolicitacaoInteresse
            context['solicitacoes_pendentes'] = SolicitacaoInteresse.objects.filter(
                status='pendente'
            ).count()
        except Exception:
            pass

        try:
            from users.models import ProjectistRequest
            context['projectist_pendentes'] = ProjectistRequest.objects.filter(
                status='pending'
            ).count()
        except Exception:
            pass

    return context
