from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Projeto, ProjetoTag, ComentarioProjeto, TodoTask, ProjetoGrupo
from canva.models import KanbanCard, KanbanColumn
from .forms import ProjetoForm  # Garantir que estamos importando o formulário
from django.db.models import Q
from datetime import datetime

# Função auxiliar para verificar se o usuário é staff
def is_staff(user):
    return user.is_staff

def projeto_lista(request):
    """View para listar todos os projetos publicados"""
    tag_slug = request.GET.get('tag')
    status = request.GET.get('status')
    
    # Base query - apenas projetos publicados
    projetos_lista = Projeto.objects.filter(publicado=True)
    
    # Filtros opcionais
    if tag_slug:
        tag = get_object_or_404(ProjetoTag, slug=tag_slug)
        projetos_lista = projetos_lista.filter(tags=tag)
        
    if status:
        projetos_lista = projetos_lista.filter(status=status)
    
    # Todas as tags para o menu lateral
    todas_tags = ProjetoTag.objects.all()
    
    # Paginação
    paginator = Paginator(projetos_lista, 12)  # 12 projetos por página
    page = request.GET.get('page')
    projetos = paginator.get_page(page)
    
    return render(request, 'projetos/projeto_lista.html', {
        'projetos': projetos,
        'tags': todas_tags,
        'tag_ativa': tag_slug,
        'status_ativo': status,
        'status_opcoes': Projeto.STATUS_CHOICES
    })

def projeto_detalhe(request, slug):
    """View para exibir detalhes de um projeto específico"""
    projeto = get_object_or_404(Projeto, slug=slug, publicado=True)
    
    # Projetos relacionados (mesma tag ou status)
    if projeto.tags.exists():
        tags = projeto.tags.all()
        projetos_relacionados = Projeto.objects.filter(
            publicado=True,
            tags__in=tags
        ).exclude(id=projeto.id).distinct()[:4]
    else:
        # Se não tem tags, buscamos pelo mesmo status
        projetos_relacionados = Projeto.objects.filter(
            publicado=True,
            status=projeto.status
        ).exclude(id=projeto.id)[:4]
    
    # Comentários aprovados e não respostas (apenas comentários principais)
    comentarios = ComentarioProjeto.objects.filter(
        projeto=projeto, 
        aprovado=True,
        comentario_pai__isnull=True
    ).select_related('autor').prefetch_related('respostas')
    
    return render(request, 'projetos/projeto_detalhe.html', {
        'projeto': projeto,
        'projetos_relacionados': projetos_relacionados,
        'comentarios': comentarios
    })

@login_required
@require_POST
def adicionar_comentario(request, projeto_id):
    """Adiciona um novo comentário em um projeto"""
    projeto = get_object_or_404(Projeto, id=projeto_id, publicado=True)
    texto = request.POST.get('texto')
    comentario_pai_id = request.POST.get('comentario_pai')
    
    if not texto:
        messages.error(request, 'O comentário não pode ser vazio.')
        return redirect('projetos:detalhe', slug=projeto.slug)
    
    # Configuramos o comentário
    comentario = ComentarioProjeto(
        projeto=projeto,
        autor=request.user,
        texto=texto
    )
    
    # Se for uma resposta a outro comentário
    if comentario_pai_id:
        try:
            comentario_pai = ComentarioProjeto.objects.get(id=comentario_pai_id)
            comentario.comentario_pai = comentario_pai
        except ComentarioProjeto.DoesNotExist:
            pass
    
    comentario.save()
    messages.success(request, 'Seu comentário foi adicionado com sucesso!')
    
    # Se for uma requisição AJAX, retornamos JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'autor': f"{request.user.first_name} {request.user.last_name}",
            'texto': texto,
            'data': comentario.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'comentario_id': comentario.id
        })
    
    # Caso contrário, redirecionamos de volta para a página do projeto
    return redirect('projetos:detalhe', slug=projeto.slug)

@login_required
@require_POST
def excluir_comentario(request, comentario_id):
    """Remove um comentário (apenas o autor ou administrador pode fazer isso)"""
    comentario = get_object_or_404(ComentarioProjeto, id=comentario_id)
    projeto = comentario.projeto
    
    # Verificar permissão (autor ou admin)
    if request.user != comentario.autor and not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para excluir este comentário.')
        return redirect('projetos:detalhe', slug=projeto.slug)
    
    comentario.delete()
    messages.success(request, 'Comentário excluído com sucesso!')
    
    # Se for uma requisição AJAX, retornamos JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    
    return redirect('projetos:detalhe', slug=projeto.slug)

@login_required
@user_passes_test(is_staff)
def projeto_novo(request):
    if request.method == 'POST':
        form = ProjetoForm(request.POST, request.FILES)
        if form.is_valid():
            projeto = form.save(commit=False)
            projeto.criado_por = request.user
            projeto.save()
            
            # Salva as relações many-to-many após salvar o objeto principal
            form.save_m2m()
            
            messages.success(request, 'Projeto criado com sucesso!')
            return redirect('projetos:detalhe', slug=projeto.slug)
    else:
        form = ProjetoForm()
    
    return render(request, 'projetos/projeto_form.html', {'form': form, 'acao': 'Criar'})

@login_required
@user_passes_test(is_staff)
def gestao_projetos(request):
    """View para a página principal (hub) de gestão de projetos"""
    
    # Estatísticas para o dashboard do hub
    total_projetos = Projeto.objects.count()
    projetos_ativos = Projeto.objects.filter(status='Ativo').count()
    projetos_concluidos = Projeto.objects.filter(status='Concluído').count()
    projetos_atrasados = Projeto.objects.filter(status='Ativo', data_conclusao__lt=timezone.now()).count()
    
    # Lista de projetos recentes para o card de projetos
    projetos_recentes = Projeto.objects.order_by('-data_atualizacao')[:5]
    
    # Cards recentes do Kanban para o card de atividades
    cards_recentes = KanbanCard.objects.select_related('responsavel', 'projeto', 'coluna').order_by('-data_atualizacao')[:5]
    
    # Informações de grupos (apenas para superusuários)
    total_grupos = 0
    total_membros = 0
    grupos_recentes = []
    
    # Grupos do usuário atual
    meus_grupos = ProjetoGrupo.objects.filter(membros=request.user).prefetch_related('membros').order_by('nome')
    
    if request.user.is_superuser:
        grupos = ProjetoGrupo.objects.all()
        total_grupos = grupos.count()
        # Contar membros únicos em todos os grupos
        membros_ids = set()
        for grupo in grupos:
            membros_ids.update(grupo.membros.values_list('id', flat=True))
        total_membros = len(membros_ids)
        
        # Grupos recentes para exibição
        grupos_recentes = ProjetoGrupo.objects.prefetch_related('membros').order_by('-data_criacao')[:3]
    
    context = {
        'total_projetos': total_projetos,
        'projetos_ativos': projetos_ativos,
        'projetos_concluidos': projetos_concluidos,
        'projetos_atrasados': projetos_atrasados,
        'projetos_recentes': projetos_recentes,
        'cards_recentes': cards_recentes,
        'total_grupos': total_grupos,
        'total_membros': total_membros,
        'grupos_recentes': grupos_recentes,
        'meus_grupos': meus_grupos,
    }
    
    return render(request, 'projetos/gestao_hub.html', context)

@login_required
def todo_list(request):
    """Exibe a lista de tarefas do usuário"""
    # Configurações de filtros e ordenação
    filtro_status = request.GET.get('status', 'all')
    filtro_prioridade = request.GET.get('prioridade', '')
    filtro_projeto = request.GET.get('projeto', '')
    filtro_grupo = request.GET.get('grupo', '')  # Novo filtro para grupo
    order_by = request.GET.get('order_by', 'data_limite')
    direction = request.GET.get('direction', 'asc')
    
    # Obter todas as tarefas do usuário atual e tarefas dos grupos aos quais pertence
    if request.user.is_superuser:
        # Superusuários podem ver todas as tarefas
        tarefas = TodoTask.objects.all()
    else:
        # Usuários comuns veem suas próprias tarefas e as tarefas dos seus grupos
        grupos_usuario = ProjetoGrupo.objects.filter(membros=request.user)
        tarefas = TodoTask.objects.filter(
            Q(usuario=request.user) | Q(grupo__in=grupos_usuario)
        ).distinct()
    
    # Aplicar filtros
    if filtro_status == 'pending':
        tarefas = tarefas.filter(concluida=False)
    elif filtro_status == 'completed':
        tarefas = tarefas.filter(concluida=True)
    
    if filtro_prioridade:
        tarefas = tarefas.filter(prioridade=filtro_prioridade)
    
    if filtro_projeto:
        tarefas = tarefas.filter(projeto_id=int(filtro_projeto))
        
    if filtro_grupo:
        tarefas = tarefas.filter(grupo_id=int(filtro_grupo))
    
    # Ordenação
    order_prefix = '' if direction == 'asc' else '-'
    if order_by == 'data_criacao':
        tarefas = tarefas.order_by(f"{order_prefix}data_criacao")
    elif order_by == 'data_limite':
        # Correto: Lidar com ordenação de datas nulas de forma compatível
        nulos = list(tarefas.filter(data_limite=None))
        com_data = list(tarefas.exclude(data_limite=None).order_by(f"{order_prefix}data_limite"))
        
        if direction == 'asc':
            tarefas = com_data + nulos
        else:
            tarefas = com_data + nulos
    elif order_by == 'prioridade':
        # Mapeamento para ordenação numérica
        priority_order = {
            'urgente': 0, 
            'alta': 1, 
            'media': 2, 
            'baixa': 3
        }
        
        # Ordene primeiro por prioridade depois por data limite
        if direction == 'asc':  # Baixa -> Urgente
            tarefas = sorted(
                tarefas,
                key=lambda t: (priority_order.get(t.prioridade, 4), 
                              t.data_limite or datetime.max.date())
            )
        else:  # Urgente -> Baixa
            tarefas = sorted(
                tarefas,
                key=lambda t: (-priority_order.get(t.prioridade, -4), 
                              t.data_limite or datetime.max.date())
            )
    elif order_by == 'titulo':
        tarefas = tarefas.order_by(f"{order_prefix}titulo")
    
    # Estatísticas
    total_tarefas = len(tarefas)
    tarefas_pendentes = sum(1 for t in tarefas if not t.concluida)
    tarefas_concluidas = sum(1 for t in tarefas if t.concluida)
    
    # Tarefas atrasadas (data limite no passado e não concluídas)
    hoje = timezone.now().date()
    tarefas_atrasadas = sum(1 for t in tarefas if t.data_limite and t.data_limite < hoje and not t.concluida)
    
    # Lista de projetos e grupos para o filtro
    projetos = Projeto.objects.filter(
        Q(responsavel=request.user) | Q(participantes=request.user)
    ).distinct()
    
    # Apenas superusuários podem ver todos os grupos
    if request.user.is_superuser:
        grupos = ProjetoGrupo.objects.all()
    else:
        grupos = ProjetoGrupo.objects.filter(membros=request.user)
    
    context = {
        'tarefas': tarefas,
        'total_tarefas': total_tarefas,
        'tarefas_pendentes': tarefas_pendentes,
        'tarefas_concluidas': tarefas_concluidas,
        'tarefas_atrasadas': tarefas_atrasadas,
        'projetos': projetos,
        'grupos': grupos,  # Adicionando grupos ao contexto
        'filtro_status': filtro_status,
        'filtro_prioridade': filtro_prioridade,
        'filtro_projeto': filtro_projeto,
        'filtro_grupo': filtro_grupo,  # Novo filtro para grupo
        'order_by': order_by,
        'direction': direction
    }
    
    return render(request, 'projetos/todo_list_simplified.html', context)

@login_required
def add_task(request):
    """Adiciona uma nova tarefa"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        prioridade = request.POST.get('prioridade', 'media')
        projeto_id = request.POST.get('projeto')
        grupo_id = request.POST.get('grupo')  # Novo campo para grupo
        data_limite_str = request.POST.get('data_limite')
        
        # Validação básica
        if not titulo:
            messages.error(request, 'O título da tarefa é obrigatório.')
            return redirect('projetos:todo_list')
        
        # Criar a tarefa
        task = TodoTask(
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade
        )
        
        # Processar atribuição - pode ser a um usuário específico ou a um grupo
        if grupo_id:
            try:
                grupo = ProjetoGrupo.objects.get(id=grupo_id)
                task.grupo = grupo
                # Quando atribuído a um grupo, o usuário pode ser deixado em branco
                if request.user.is_superuser:
                    task.usuario = None
                else:
                    task.usuario = request.user  # Se não for superuser, ainda vincula ao próprio usuário
            except ProjetoGrupo.DoesNotExist:
                task.usuario = request.user
        else:
            task.usuario = request.user
        
        # Processar projeto se for informado
        if projeto_id:
            try:
                projeto = Projeto.objects.get(id=projeto_id)
                task.projeto = projeto
            except Projeto.DoesNotExist:
                pass
        
        # Processar data limite se for informada
        if data_limite_str:
            try:
                data_limite = datetime.strptime(data_limite_str, '%Y-%m-%d').date()
                task.data_limite = data_limite
            except ValueError:
                pass
        
        # Salvar a tarefa
        task.save()
        
        # Adicionar mensagem de sucesso
        if task.grupo:
            messages.success(request, f'Tarefa "{titulo}" adicionada com sucesso para o grupo {task.grupo.nome}!')
        else:
            messages.success(request, f'Tarefa "{titulo}" adicionada com sucesso!')
        
    return redirect('projetos:todo_list')

@login_required
def update_task(request, task_id):
    """Atualiza uma tarefa existente"""
    # Obtemos a tarefa primeiro para verificar permissões
    task = get_object_or_404(TodoTask, id=task_id)
    
    # Verificar se a tarefa pertence a um grupo
    if task.grupo:
        # Se é tarefa de grupo, verificar se o usuário é membro desse grupo
        is_group_member = request.user in task.grupo.membros.all()
        is_task_owner = task.usuario == request.user
        
        # Verificar se é uma requisição AJAX para toggle de conclusão - isso qualquer membro pode fazer
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
            if is_group_member or is_task_owner or request.user.is_superuser:
                concluida = request.POST.get('concluida') in ['true', 'on']
                task.concluida = concluida
                task.save()
                return JsonResponse({'status': 'success', 'concluida': task.concluida})
            else:
                return JsonResponse({'status': 'error', 'message': 'Sem permissão'}, status=403)
        
        # Para edições completas, apenas superusuários podem editar tarefas de grupo
        elif not request.user.is_superuser:
            messages.error(request, 'Apenas administradores podem editar detalhes das tarefas de grupo')
            return redirect('projetos:todo_list')
    else:
        # Se não é tarefa de grupo, verificar permissão normal - apenas o proprietário ou superuser
        if task.usuario != request.user and not request.user.is_superuser:
            messages.error(request, 'Você não tem permissão para editar esta tarefa')
            return redirect('projetos:todo_list')
    
    # Verificar se é uma requisição AJAX para toggle de conclusão (caso não seja tarefa de grupo)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        concluida = request.POST.get('concluida') in ['true', 'on']
        task.concluida = concluida
        task.save()
        
        return JsonResponse({'status': 'success', 'concluida': task.concluida})
    
    # Processamento de formulário normal para atualização completa
    if request.method == 'POST':
        task.titulo = request.POST.get('titulo', task.titulo)
        task.descricao = request.POST.get('descricao', '')
        task.prioridade = request.POST.get('prioridade', 'media')
        
        # Processar projeto
        projeto_id = request.POST.get('projeto', '')
        if projeto_id:
            try:
                projeto = Projeto.objects.get(id=projeto_id)
                task.projeto = projeto
            except Projeto.DoesNotExist:
                task.projeto = None
        else:
            task.projeto = None
            
        # Processar grupo
        grupo_id = request.POST.get('grupo', '')
        if grupo_id:
            try:
                grupo = ProjetoGrupo.objects.get(id=grupo_id)
                task.grupo = grupo
                # Se a tarefa for atribuída a um grupo e o usuário for superusuário,
                # o campo usuario pode ser definido como None
                if request.user.is_superuser:
                    task.usuario = None
            except ProjetoGrupo.DoesNotExist:
                task.grupo = None
        else:
            task.grupo = None
            
        # Processar data limite
        data_limite_str = request.POST.get('data_limite', '')
        if data_limite_str:
            try:
                data_limite = datetime.strptime(data_limite_str, '%Y-%m-%d').date()
                task.data_limite = data_limite
            except ValueError:
                task.data_limite = None
        else:
            task.data_limite = None
        
        # Processar status de conclusão
        task.concluida = 'concluida' in request.POST
        task.save()
        
    return redirect('projetos:todo_list')

@login_required
def delete_task(request, task_id):
    """Exclui uma tarefa"""
    # Obtemos a tarefa sem filtrar pelo usuário para verificar permissões depois
    task = get_object_or_404(TodoTask, id=task_id)
    
    # Verifica permissões:
    # 1. Se a tarefa tem grupo e o usuário não é superusuário, não pode excluir
    # 2. Se a tarefa não tem grupo, apenas o dono pode excluir
    if task.grupo and not request.user.is_superuser:
        messages.error(request, 'Apenas administradores podem excluir tarefas de grupo')
        return redirect('projetos:todo_list')
    elif not task.grupo and task.usuario != request.user:
        messages.error(request, 'Você não tem permissão para excluir esta tarefa')
        return redirect('projetos:todo_list')
    
    if request.method == 'POST':
        task_title = task.titulo
        task_grupo = task.grupo.nome if task.grupo else None
        task.delete()
        
        if task_grupo:
            messages.success(request, f'Tarefa "{task_title}" do grupo {task_grupo} excluída com sucesso!')
        else:
            messages.success(request, f'Tarefa "{task_title}" excluída com sucesso!')
    
    return redirect('projetos:todo_list')

# Views para gerenciamento de grupos de projetos

@login_required
@user_passes_test(lambda u: u.is_superuser)
@user_passes_test(lambda u: u.is_superuser)
def grupo_lista(request):
    """Lista todos os grupos de projetos - apenas superusuários"""
    grupos = ProjetoGrupo.objects.all().order_by('nome')
    
    # Opção para filtrar por busca
    termo_busca = request.GET.get('busca', '')
    if termo_busca:
        grupos = grupos.filter(
            Q(nome__icontains=termo_busca) | 
            Q(descricao__icontains=termo_busca)
        )
    
    # Paginação
    paginator = Paginator(grupos, 10)
    page_number = request.GET.get('page')
    grupos_paginados = paginator.get_page(page_number)
    
    context = {
        'grupos': grupos_paginados,
        'termo_busca': termo_busca,
        'titulo': 'Grupos de Projetos'
    }
    
    return render(request, 'projetos/grupo_lista.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@user_passes_test(lambda u: u.is_superuser)
def grupo_novo(request):
    """Cria um novo grupo de projetos - apenas superusuários"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        membros_ids = request.POST.getlist('membros')
        projetos_ids = request.POST.getlist('projetos')
        
        if not nome:
            messages.error(request, 'O nome do grupo é obrigatório.')
            return redirect('projetos:grupo_novo')
        
        # Criar o grupo
        grupo = ProjetoGrupo(
            nome=nome,
            descricao=descricao,
            criado_por=request.user
        )
        grupo.save()
        
        # Adicionar membros
        if membros_ids:
            membros = User.objects.filter(id__in=membros_ids)
            grupo.membros.add(*membros)
        
        # Adicionar projetos
        if projetos_ids:
            projetos = Projeto.objects.filter(id__in=projetos_ids)
            grupo.projetos.add(*projetos)
        
        messages.success(request, f'Grupo "{nome}" criado com sucesso!')
        return redirect('projetos:grupos_lista')
    
    # Opções para o formulário
    usuarios = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    projetos = Projeto.objects.all().order_by('titulo')
    
    context = {
        'usuarios': usuarios,
        'projetos': projetos,
        'status_opcoes': Projeto.STATUS_CHOICES,
        'titulo': 'Novo Grupo de Projetos'
    }
    
    return render(request, 'projetos/grupo_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def grupo_detalhe(request, grupo_id):
    """Mostra detalhes de um grupo de projetos - apenas superusuários"""
    grupo = get_object_or_404(ProjetoGrupo, id=grupo_id)
    
    # Tarefas associadas ao grupo
    tarefas = TodoTask.objects.filter(grupo=grupo)
    
    context = {
        'grupo': grupo,
        'tarefas': tarefas,
        'titulo': f'Detalhes do Grupo: {grupo.nome}'
    }
    
    return render(request, 'projetos/grupo_detalhe.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def grupo_editar(request, grupo_id):
    """Edita um grupo de projetos - apenas superusuários"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    grupo = get_object_or_404(ProjetoGrupo, id=grupo_id)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        membros_ids = request.POST.getlist('membros')
        projetos_ids = request.POST.getlist('projetos')
        
        if not nome:
            messages.error(request, 'O nome do grupo é obrigatório.')
            return redirect('projetos:grupo_editar', grupo_id=grupo_id)
        
        # Atualizar campos básicos
        grupo.nome = nome
        grupo.descricao = descricao
        grupo.save()
        
        # Atualizar membros
        grupo.membros.clear()
        if membros_ids:
            membros = User.objects.filter(id__in=membros_ids)
            grupo.membros.add(*membros)
        
        # Atualizar projetos
        grupo.projetos.clear()
        if projetos_ids:
            projetos = Projeto.objects.filter(id__in=projetos_ids)
            grupo.projetos.add(*projetos)
        
        messages.success(request, f'Grupo "{nome}" atualizado com sucesso!')
        return redirect('projetos:grupos_lista')
    
    # Opções para o formulário
    usuarios = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    projetos = Projeto.objects.all().order_by('titulo')
    
    # Valores pré-selecionados
    membros_selecionados = grupo.membros.all().values_list('id', flat=True)
    projetos_selecionados = grupo.projetos.all().values_list('id', flat=True)
    
    context = {
        'grupo': grupo,
        'usuarios': usuarios,
        'projetos': projetos,
        'membros_selecionados': membros_selecionados,
        'projetos_selecionados': projetos_selecionados,
        'status_opcoes': Projeto.STATUS_CHOICES,
        'titulo': f'Editar Grupo: {grupo.nome}',
        'acao': 'Editar'
    }
    
    return render(request, 'projetos/grupo_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def grupo_excluir(request, grupo_id):
    """Excluir um grupo de projetos - apenas superusuários"""
    grupo = get_object_or_404(ProjetoGrupo, id=grupo_id)
    
    if request.method == 'POST':
        nome = grupo.nome
        grupo.delete()
        messages.success(request, f'Grupo "{nome}" excluído com sucesso!')
        return redirect('projetos:grupos_lista')
    
    return render(request, 'projetos/grupo_confirmar_exclusao.html', {'grupo': grupo})
