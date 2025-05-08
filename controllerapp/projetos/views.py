from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Projeto, ProjetoTag, ComentarioProjeto

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
