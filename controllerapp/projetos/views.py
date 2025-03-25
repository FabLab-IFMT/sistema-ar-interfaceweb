from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Projeto, ProjetoTag

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
    
    return render(request, 'projetos/projeto_detalhe.html', {
        'projeto': projeto,
        'projetos_relacionados': projetos_relacionados
    })
