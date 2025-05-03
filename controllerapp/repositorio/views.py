from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Resource, ResourceCategory, ResourceComment
from .forms import ResourceForm, ResourceCommentForm
from projetos.models import Projeto

def index(request):
    """Página inicial do repositório de recursos"""
    # Buscar categorias para o menu lateral
    categories = ResourceCategory.objects.all()
    
    # Buscar recursos destacados
    featured_resources = Resource.objects.filter(featured=True).order_by('-created_at')
    
    # Se o usuário estiver logado, mostrar recursos visíveis para ele
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Superusuários vêem tudo
            resources = Resource.objects.all()
        else:
            # Usuários comuns vêem recursos públicos, recursos de times se forem staff, e recursos de projetos dos quais são membros
            projects_as_member = Projeto.objects.filter(
                Q(responsavel=request.user) | Q(participantes=request.user)
            )
            
            resources = Resource.objects.filter(
                Q(visibility='public') |
                (Q(visibility='members') & Q(project__in=projects_as_member)) |
                (Q(visibility='team') & Q(request.user.is_staff))
            )
    else:
        # Para visitantes, só mostrar recursos públicos
        resources = Resource.objects.filter(visibility='public')
    
    # Aplicar filtros
    category_slug = request.GET.get('category')
    resource_type = request.GET.get('type')
    project_id = request.GET.get('project')
    search_query = request.GET.get('q')
    
    if category_slug:
        category = get_object_or_404(ResourceCategory, slug=category_slug)
        resources = resources.filter(category=category)
        
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
        
    if project_id:
        project = get_object_or_404(Projeto, id=project_id)
        resources = resources.filter(project=project)
        
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Ordenar por mais recentes
    resources = resources.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'featured_resources': featured_resources[:4],
        'resources': page_obj,
        'resource_types': Resource.RESOURCE_TYPES,
        'selected_category': category_slug,
        'selected_type': resource_type,
        'selected_project': project_id,
        'search_query': search_query,
    }
    
    return render(request, 'repositorio/index.html', context)

def project_resources(request, project_slug):
    """Mostra recursos de um projeto específico"""
    project = get_object_or_404(Projeto, slug=project_slug)
    
    # Verificar se o projeto é publicado ou se o usuário tem acesso
    if not project.publicado and not request.user.is_superuser:
        if not request.user.is_authenticated or (
            request.user != project.responsavel and
            request.user not in project.participantes.all()
        ):
            raise Http404("Projeto não encontrado")
    
    # Definir quais recursos o usuário pode ver
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user == project.responsavel:
            # Superuser e responsável vêem tudo
            resources = project.resources.all()
        elif request.user in project.participantes.all():
            # Membros vêem recursos públicos e para membros
            resources = project.resources.filter(
                Q(visibility='public') | Q(visibility='members')
            )
        else:
            # Usuários logados não membros vêem apenas recursos públicos
            resources = project.resources.filter(visibility='public')
    else:
        # Visitantes vêem apenas recursos públicos
        resources = project.resources.filter(visibility='public')
    
    # Aplicar filtros
    category_slug = request.GET.get('category')
    resource_type = request.GET.get('type')
    search_query = request.GET.get('q')
    
    if category_slug:
        category = get_object_or_404(ResourceCategory, slug=category_slug)
        resources = resources.filter(category=category)
        
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
        
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Ordenar por mais recentes
    resources = resources.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Verificar se o usuário é membro para mostrar botão de adicionar
    is_member = request.user.is_authenticated and (
        request.user.is_superuser or 
        request.user == project.responsavel or 
        request.user in project.participantes.all()
    )
    
    context = {
        'project': project,
        'resources': page_obj,
        'categories': ResourceCategory.objects.all(),
        'resource_types': Resource.RESOURCE_TYPES,
        'selected_category': category_slug,
        'selected_type': resource_type,
        'search_query': search_query,
        'is_member': is_member,
    }
    
    return render(request, 'repositorio/project_resources.html', context)

def resource_detail(request, slug):
    """Mostra detalhes de um recurso específico"""
    resource = get_object_or_404(Resource, slug=slug)
    
    # Verificar se o usuário tem permissão para visualizar
    if not resource.can_view(request.user):
        return HttpResponseForbidden("Você não tem permissão para visualizar este recurso")
    
    # Formulário para comentários
    comment_form = None
    if request.user.is_authenticated:
        comment_form = ResourceCommentForm()
        
        # Processar comentário submetido
        if request.method == 'POST' and 'comment-submit' in request.POST:
            comment_form = ResourceCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.resource = resource
                comment.user = request.user
                comment.save()
                messages.success(request, "Comentário adicionado com sucesso!")
                return redirect('repositorio:resource_detail', slug=resource.slug)
    
    # Verificar se o usuário pode editar
    can_edit = resource.can_edit(request.user)
    
    # Buscar comentários
    comments = resource.comments.all().select_related('user')
    
    context = {
        'resource': resource,
        'can_edit': can_edit,
        'comment_form': comment_form,
        'comments': comments,
    }
    
    return render(request, 'repositorio/resource_detail.html', context)

@login_required
def resource_create(request, project_slug=None):
    """Criar um novo recurso"""
    # Se project_slug for fornecido, buscar o projeto
    project = None
    if project_slug:
        project = get_object_or_404(Projeto, slug=project_slug)
        
        # Verificar se o usuário é membro do projeto
        if not (request.user.is_superuser or request.user == project.responsavel or request.user in project.participantes.all()):
            return HttpResponseForbidden("Você não tem permissão para adicionar recursos a este projeto")
    
    # Se não houver projeto específico, mostrar lista de projetos para escolher
    if not project:
        if request.user.is_superuser:
            projects = Projeto.objects.all()
        else:
            projects = Projeto.objects.filter(
                Q(responsavel=request.user) | Q(participantes=request.user)
            )
            
        if not projects.exists():
            messages.error(request, "Você não tem permissão para adicionar recursos a nenhum projeto")
            return redirect('repositorio:index')
            
        if projects.count() == 1:
            # Se o usuário só tem um projeto, ir direto para o formulário
            project = projects.first()
        else:
            # Mostrar página para escolher o projeto
            context = {
                'projects': projects,
            }
            return render(request, 'repositorio/select_project.html', context)
    
    # Processar formulário
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, project=project, user=request.user)
        if form.is_valid():
            resource = form.save()
            messages.success(request, "Recurso criado com sucesso!")
            return redirect('repositorio:resource_detail', slug=resource.slug)
    else:
        form = ResourceForm(project=project, user=request.user)
    
    context = {
        'form': form,
        'project': project,
        'creating': True,
    }
    
    return render(request, 'repositorio/resource_form.html', context)

@login_required
def resource_edit(request, slug):
    """Editar um recurso existente"""
    resource = get_object_or_404(Resource, slug=slug)
    
    # Verificar permissão para editar
    if not resource.can_edit(request.user):
        return HttpResponseForbidden("Você não tem permissão para editar este recurso")
    
    # Processar formulário
    if request.method == 'POST':
        form = ResourceForm(
            request.POST, 
            request.FILES,
            instance=resource,
            project=resource.project, 
            user=request.user
        )
        if form.is_valid():
            resource = form.save()
            messages.success(request, "Recurso atualizado com sucesso!")
            return redirect('repositorio:resource_detail', slug=resource.slug)
    else:
        form = ResourceForm(instance=resource, project=resource.project, user=request.user)
    
    context = {
        'form': form,
        'resource': resource,
        'project': resource.project,
        'creating': False,
    }
    
    return render(request, 'repositorio/resource_form.html', context)

@login_required
@require_POST
def resource_delete(request, slug):
    """Excluir um recurso"""
    resource = get_object_or_404(Resource, slug=slug)
    
    # Verificar permissão para excluir (apenas superuser ou criador ou responsável pelo projeto)
    if not (request.user.is_superuser or request.user == resource.created_by or request.user == resource.project.responsavel):
        return HttpResponseForbidden("Você não tem permissão para excluir este recurso")
    
    project = resource.project
    resource.delete()
    messages.success(request, "Recurso excluído com sucesso!")
    
    # Redirecionar para a lista de recursos do projeto
    return redirect('repositorio:project_resources', project_slug=project.slug)

@login_required
@require_POST
def comment_delete(request, comment_id):
    """Excluir um comentário"""
    comment = get_object_or_404(ResourceComment, id=comment_id)
    
    # Verificar permissão para excluir (apenas superuser ou autor do comentário ou responsável pelo projeto)
    if not (request.user.is_superuser or request.user == comment.user or request.user == comment.resource.project.responsavel):
        return HttpResponseForbidden("Você não tem permissão para excluir este comentário")
    
    resource_slug = comment.resource.slug
    comment.delete()
    
    # Se for uma solicitação AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, "Comentário excluído com sucesso!")
    return redirect('repositorio:resource_detail', slug=resource_slug)
