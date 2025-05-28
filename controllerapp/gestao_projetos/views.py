from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .models import GrupoProjetos
from .forms import GrupoProjetosForm

def is_superuser(user):
    """Verifica se o usuário é superuser"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def lista_grupos_projetos(request):
    """Listar todos os grupos de projetos (apenas superuser)"""
    grupos = GrupoProjetos.objects.all()
    return render(request, 'gestao_projetos/grupos_projetos/lista.html', {
        'grupos': grupos,
        'titulo': 'Grupos de Projetos'
    })

@login_required
@user_passes_test(is_superuser)
def criar_grupo_projetos(request):
    """Criar um novo grupo de projetos (apenas superuser)"""
    if request.method == 'POST':
        form = GrupoProjetosForm(request.POST)
        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.criado_por = request.user
            grupo.save()
            # Para salvar os relacionamentos ManyToMany
            form.save_m2m()
            messages.success(request, 'Grupo de projetos criado com sucesso.')
            return redirect('gestao_projetos:lista_grupos_projetos')
    else:
        form = GrupoProjetosForm()
    
    return render(request, 'gestao_projetos/grupos_projetos/form.html', {
        'form': form,
        'titulo': 'Criar Grupo de Projetos',
        'botao': 'Criar'
    })

@login_required
@user_passes_test(is_superuser)
def editar_grupo_projetos(request, slug):
    """Editar um grupo de projetos existente (apenas superuser)"""
    grupo = get_object_or_404(GrupoProjetos, slug=slug)
    
    if request.method == 'POST':
        form = GrupoProjetosForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo de projetos atualizado com sucesso.')
            return redirect('gestao_projetos:lista_grupos_projetos')
    else:
        form = GrupoProjetosForm(instance=grupo)
    
    return render(request, 'gestao_projetos/grupos_projetos/form.html', {
        'form': form,
        'grupo': grupo,
        'titulo': 'Editar Grupo de Projetos',
        'botao': 'Atualizar'
    })

@login_required
@user_passes_test(is_superuser)
def excluir_grupo_projetos(request, slug):
    """Excluir um grupo de projetos (apenas superuser)"""
    grupo = get_object_or_404(GrupoProjetos, slug=slug)
    
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de projetos excluído com sucesso.')
        return redirect('gestao_projetos:lista_grupos_projetos')
    
    return render(request, 'gestao_projetos/grupos_projetos/confirmar_exclusao.html', {
        'grupo': grupo,
        'titulo': 'Confirmar Exclusão'
    })

@login_required
@user_passes_test(is_superuser)
def detalhes_grupo_projetos(request, slug):
    """Visualizar detalhes de um grupo de projetos (apenas superuser)"""
    grupo = get_object_or_404(GrupoProjetos, slug=slug)
    
    return render(request, 'gestao_projetos/grupos_projetos/detalhes.html', {
        'grupo': grupo,
        'titulo': f'Grupo: {grupo.nome}'
    })
