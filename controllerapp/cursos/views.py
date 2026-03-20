from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import Curso, CategoriaCurso
from projetos.models import Projeto


def curso_lista(request):
    """Lista pública de cursos do laboratório."""
    cursos = Curso.objects.filter(publicado=True).select_related('categoria', 'instrutor')

    # Filtros
    q          = request.GET.get('q', '')
    status     = request.GET.get('status', '')
    categoria  = request.GET.get('categoria', '')

    if q:
        cursos = cursos.filter(
            Q(titulo__icontains=q) | Q(descricao_curta__icontains=q)
        )
    if status:
        cursos = cursos.filter(status=status)
    if categoria:
        cursos = cursos.filter(categoria__slug=categoria)

    categorias      = CategoriaCurso.objects.all()
    cursos_destaque = Curso.objects.filter(publicado=True, destaque=True)[:3]

    context = {
        'cursos': cursos,
        'categorias': categorias,
        'cursos_destaque': cursos_destaque,
        'q': q,
        'status_filtro': status,
        'categoria_filtro': categoria,
        'status_choices': Curso.STATUS_CHOICES,
        'total': cursos.count(),
    }
    return render(request, 'cursos/lista.html', context)


def curso_detalhe(request, slug):
    """Detalhe público de um curso."""
    curso = get_object_or_404(Curso, slug=slug, publicado=True)
    projetos_rel = curso.projetos_relacionados.filter(publicado=True)
    outros_cursos = Curso.objects.filter(
        publicado=True, categoria=curso.categoria
    ).exclude(pk=curso.pk)[:4]

    context = {
        'curso': curso,
        'projetos_relacionados': projetos_rel,
        'outros_cursos': outros_cursos,
    }
    return render(request, 'cursos/detalhe.html', context)


# ── Admin views (dentro do painel de gestão) ──

def is_gestao(user):
    if user.is_superuser or user.is_staff:
        return True
    try:
        return user.acesso_gestao.tem_acesso
    except Exception:
        return False


def can_manage_cursos(user):
    return is_gestao(user) or user.has_role('projetista') or user.has_role('gestor')


@login_required
@user_passes_test(can_manage_cursos)
def admin_cursos(request):
    """Admin: lista e gerencia cursos."""
    cursos = Curso.objects.all().select_related('categoria', 'instrutor')

    q = request.GET.get('q', '')
    if q:
        cursos = cursos.filter(Q(titulo__icontains=q) | Q(descricao_curta__icontains=q))

    filtro_status = request.GET.get('status', '')
    if filtro_status:
        cursos = cursos.filter(status=filtro_status)

    context = {
        'titulo': 'Gerenciar Cursos',
        'cursos': cursos,
        'q': q,
        'filtro_status': filtro_status,
        'status_choices': Curso.STATUS_CHOICES,
        'total': cursos.count(),
    }
    return render(request, 'gestao/admin_cursos.html', context)


@login_required
@user_passes_test(can_manage_cursos)
def admin_curso_form(request, curso_id=None):
    """Admin: criar ou editar um curso."""
    curso = None
    if curso_id:
        curso = get_object_or_404(Curso, id=curso_id)

    categorias = CategoriaCurso.objects.all().order_by('ordem', 'nome')
    from django.contrib.auth import get_user_model
    User = get_user_model()
    instrutores = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    projetos = Projeto.objects.filter(publicado=True).order_by('-data_criacao')

    if request.method == 'POST':
        titulo           = request.POST.get('titulo', '').strip()
        descricao_curta  = request.POST.get('descricao_curta', '').strip()
        descricao        = request.POST.get('descricao', '').strip()
        status           = request.POST.get('status', 'planejado')
        carga_horaria    = request.POST.get('carga_horaria') or None
        data_inicio      = request.POST.get('data_inicio') or None
        data_fim         = request.POST.get('data_fim') or None
        vagas            = request.POST.get('vagas') or None
        publicado        = 'publicado' in request.POST
        destaque         = 'destaque' in request.POST
        mostrar_na_home  = 'mostrar_na_home' in request.POST
        categoria_id     = request.POST.get('categoria') or None
        instrutor_id     = request.POST.get('instrutor') or None
        proj_ids         = request.POST.getlist('projetos_relacionados')

        if not titulo:
            messages.error(request, "O título é obrigatório.")
            return render(request, 'gestao/admin_curso_form.html', {
                'curso': curso, 'categorias': categorias,
                'instrutores': instrutores, 'projetos': projetos,
                'titulo': 'Editar Curso' if curso else 'Novo Curso',
            })

        if not curso:
            curso = Curso()

        curso.titulo          = titulo
        curso.descricao_curta = descricao_curta
        curso.descricao       = descricao
        curso.status          = status
        curso.publicado       = publicado
        curso.destaque        = destaque
        curso.mostrar_na_home = mostrar_na_home
        curso.carga_horaria   = int(carga_horaria) if carga_horaria else None
        curso.data_inicio     = data_inicio or None
        curso.data_fim        = data_fim or None
        curso.vagas           = int(vagas) if vagas else None
        curso.criado_por      = curso.criado_por or request.user

        try:
            curso.categoria = CategoriaCurso.objects.get(id=categoria_id) if categoria_id else None
        except CategoriaCurso.DoesNotExist:
            curso.categoria = None

        try:
            curso.instrutor = User.objects.get(pk=instrutor_id) if instrutor_id else None
        except User.DoesNotExist:
            curso.instrutor = None

        if 'imagem' in request.FILES:
            curso.imagem = request.FILES['imagem']

        curso.save()

        # Projetos relacionados
        curso.projetos_relacionados.set(
            Projeto.objects.filter(id__in=proj_ids) if proj_ids else []
        )

        action = "atualizado" if curso_id else "criado"
        messages.success(request, f"Curso '{curso.titulo}' {action} com sucesso.")
        return redirect('cursos:admin_cursos')

    context = {
        'curso': curso,
        'categorias': categorias,
        'instrutores': instrutores,
        'projetos': projetos,
        'titulo': 'Editar Curso' if curso else 'Novo Curso',
        'status_choices': Curso.STATUS_CHOICES,
        'proj_selecionados': set(curso.projetos_relacionados.values_list('id', flat=True)) if curso else set(),
    }
    return render(request, 'gestao/admin_curso_form.html', context)


@login_required
@user_passes_test(can_manage_cursos)
def admin_curso_toggle_publicado(request, curso_id):
    from django.views.decorators.http import require_POST
    curso = get_object_or_404(Curso, id=curso_id)
    curso.publicado = not curso.publicado
    curso.save(update_fields=['publicado'])
    messages.success(request, f"Curso '{curso.titulo}' {'publicado' if curso.publicado else 'despublicado'}.")
    return redirect('cursos:admin_cursos')


@login_required
@user_passes_test(can_manage_cursos)
def admin_curso_deletar(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == 'POST':
        nome = curso.titulo
        curso.delete()
        messages.success(request, f"Curso '{nome}' excluído.")
        return redirect('cursos:admin_cursos')
    return render(request, 'gestao/admin_curso_confirmar_exclusao.html', {'curso': curso})
