import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, Http404, HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import models  # Adicionando a importação necessária

from .models import Resource, ResourceCategory, ResourceComment, ResourceFile
from .forms import ResourceForm, ResourceCommentForm
from projetos.models import Projeto

import os
import mimetypes

@login_required
def index(request):
    """Página inicial do repositório de recursos"""
    # Filtros e ordenação
    category_filter = request.GET.get('category')
    type_filter = request.GET.get('type')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', '-created_at')  # Padrão: mais recentes primeiro
    
    # Busca de recursos
    if request.user.is_superuser:
        # Superusuários veem todos os recursos
        resources = Resource.objects.all()
    else:
        # Usuários normais veem apenas recursos públicos e os que têm permissão
        # Corrigindo o problema aqui - não podemos usar condições booleanas diretas
        resources = Resource.objects.filter(
            # Recursos públicos OU recursos onde o usuário é membro do projeto
            models.Q(visibility='public') | 
            models.Q(project__responsavel=request.user) |
            models.Q(project__participantes=request.user)
        ).distinct()
    
    # Aplicar filtros adicionais
    if category_filter:
        try:
            category = ResourceCategory.objects.get(slug=category_filter)
            resources = resources.filter(category=category)
        except ResourceCategory.DoesNotExist:
            logging.warning("Categoria %s não encontrada ao filtrar recursos", category_filter)
    
    if type_filter:
        resources = resources.filter(resource_type=type_filter)
    
    if search_query:
        resources = resources.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(tags__icontains=search_query)
        )
    
    # Ordenar os resultados
    resources = resources.order_by(sort_by)
    
    # Paginação
    paginator = Paginator(resources, 12)  # 12 recursos por página
    page = request.GET.get('page')
    resources_page = paginator.get_page(page)
    
    # Contexto da página
    context = {
        'resources': resources_page,
        'categories': ResourceCategory.objects.all(),
        'resource_types': Resource.RESOURCE_TYPES,
        'selected_category': category_filter,
        'selected_type': type_filter,
        'search_query': search_query
    }
    
    return render(request, 'repositorio/index.html', context)

@login_required
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

@login_required
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
        form = ResourceForm(request.POST, project=project, user=request.user)
        if form.is_valid():
            resource = form.save()
            
            # Processar os arquivos enviados - agora diretamente do request.FILES
            files = request.FILES.getlist('files')
            for file in files:
                ResourceFile.objects.create(
                    resource=resource,
                    file=file,
                    # O título será definido automaticamente pelo nome do arquivo no método save do modelo
                )
            
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
            instance=resource,
            project=resource.project, 
            user=request.user
        )
        if form.is_valid():
            resource = form.save()
            
            # Processar os arquivos enviados - da mesma forma que na criação
            files = request.FILES.getlist('files')
            for file in files:
                ResourceFile.objects.create(
                    resource=resource,
                    file=file,
                    # O título será definido automaticamente pelo nome do arquivo
                )
            
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

# Adicionar nova view para excluir arquivos individuais
@login_required
@require_POST
def resource_file_delete(request, file_id):
    """Excluir um arquivo específico de um recurso"""
    resource_file = get_object_or_404(ResourceFile, id=file_id)
    resource = resource_file.resource
    
    # Verificar permissão para excluir
    if not resource.can_edit(request.user):
        return HttpResponseForbidden("Você não tem permissão para excluir arquivos deste recurso")
    
    # Excluir o arquivo
    resource_file.delete()
    
    # Retornar JSON para solicitações AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, "Arquivo excluído com sucesso!")
    return redirect('repositorio:resource_detail', slug=resource.slug)

@login_required
def download_file(request, file_id):
    """Download de arquivo com verificação de permissão"""
    file_obj = get_object_or_404(ResourceFile, id=file_id)
    resource = file_obj.resource
    
    # Verificar permissão para baixar o arquivo
    if not resource.can_view(request.user):
        return HttpResponseForbidden("Você não tem permissão para baixar este arquivo.")
    
    # Verificar se o arquivo existe fisicamente
    file_path = file_obj.file.path
    if not os.path.exists(file_path):
        raise Http404("O arquivo solicitado não está disponível.")
    
    # Determinar o tipo MIME do arquivo ou usar um genérico
    content_type, encoding = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Abrir o arquivo e prepará-lo para download
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response

@login_required
def add_comment(request, resource_id):
    """Adiciona um comentário a um recurso"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Verificar se o usuário tem permissão para ver este recurso
    if not resource.can_view(request.user):
        return HttpResponseForbidden("Você não tem permissão para comentar neste recurso.")
    
    if request.method == 'POST':
        comment_text = request.POST.get('text')
        
        if comment_text and comment_text.strip():
            # Criar o comentário
            comment = ResourceComment.objects.create(
                resource=resource,
                user=request.user,
                text=comment_text
            )
            
            # Verificar se é uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment': {
                        'id': comment.id,
                        'text': comment.text,
                        'user': f"{comment.user.first_name} {comment.user.last_name}",
                        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
                    }
                })
            
            messages.success(request, "Comentário adicionado com sucesso!")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'O comentário não pode estar vazio'
                }, status=400)
            
            messages.error(request, "O comentário não pode estar vazio.")
    
    # Redirecionar de volta para a página do recurso
    return redirect('repositorio:resource_detail', slug=resource.slug)

@login_required
@require_POST
def delete_comment(request, comment_id):
    """Excluir um comentário"""
    comment = get_object_or_404(ResourceComment, id=comment_id)
    resource = comment.resource
    
    # Verificar permissão: o próprio autor, responsável pelo projeto ou superusuário
    if (request.user == comment.user or 
        request.user == resource.project.responsavel or 
        request.user.is_superuser):
        
        comment.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        messages.success(request, "Comentário excluído com sucesso!")
        return redirect('repositorio:resource_detail', slug=resource.slug)
    
    # Não tem permissão
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': 'Você não tem permissão para excluir este comentário'
        }, status=403)
    
    return HttpResponseForbidden("Você não tem permissão para excluir este comentário.")
