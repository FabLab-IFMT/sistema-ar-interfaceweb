from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Material, Membro, CategoriaServico, Servico, SolicitacaoOrcamento
from .forms import SolicitacaoOrcamentoForm

# Create your views here.

def equipamentos(request):
    materiais = Material.objects.all()
    return render(request, 'equipamentos.html', {'materiais': materiais})

def membros(request):
    membros_ativos = Membro.objects.filter(ativo=True).order_by('ordem', 'nome')
    return render(request, 'membros.html', {'membros': membros_ativos})

def servicos(request):
    categorias = CategoriaServico.objects.all()
    servicos_destaque = Servico.objects.filter(destaque=True, disponivel=True)
    
    categoria_selecionada = request.GET.get('categoria')
    if categoria_selecionada:
        try:
            categoria = CategoriaServico.objects.get(id=categoria_selecionada)
            servicos_lista = Servico.objects.filter(categoria=categoria, disponivel=True)
        except:
            servicos_lista = Servico.objects.filter(disponivel=True)
    else:
        servicos_lista = Servico.objects.filter(disponivel=True)
    
    # Paginação
    paginator = Paginator(servicos_lista, 6)
    page = request.GET.get('page')
    servicos = paginator.get_page(page)
    
    context = {
        'categorias': categorias,
        'servicos': servicos,
        'servicos_destaque': servicos_destaque,
        'categoria_selecionada': categoria_selecionada
    }
    return render(request, 'servicos.html', context)

def detalhe_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, disponivel=True)
    form = SolicitacaoOrcamentoForm(initial={'servico': servico})
    
    if request.method == 'POST':
        form = SolicitacaoOrcamentoForm(request.POST, request.FILES)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            if request.user.is_authenticated:
                solicitacao.usuario = request.user
            solicitacao.save()
            messages.success(request, 'Sua solicitação de orçamento foi enviada com sucesso! Entraremos em contato em breve.')
            return redirect('options:detalhe_servico', servico_id=servico.id)
    
    servicos_relacionados = Servico.objects.filter(categoria=servico.categoria, disponivel=True).exclude(id=servico.id)[:3]
    
    context = {
        'servico': servico,
        'form': form,
        'servicos_relacionados': servicos_relacionados
    }
    return render(request, 'detalhe_servico.html', context)

@login_required
def minhas_solicitacoes(request):
    solicitacoes = SolicitacaoOrcamento.objects.filter(usuario=request.user)
    return render(request, 'minhas_solicitacoes.html', {'solicitacoes': solicitacoes})

@login_required
def solicitacao_detalhe(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoOrcamento, id=solicitacao_id)
    
    # Verificar se o usuário atual é o dono da solicitação ou é staff
    if request.user != solicitacao.usuario and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para visualizar esta solicitação.")
        return redirect('options:minhas_solicitacoes')
    
    return render(request, 'solicitacao_detalhe.html', {
        'solicitacao': solicitacao
    })
