from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Categoria, Item, Emprestimo
from .forms import ItemForm, CategoriaForm, EmprestimoForm, DevolucaoEmprestimoForm

@staff_member_required
def inventario_dashboard(request):
    """Página inicial do inventário com estatísticas gerais"""
    total_itens = Item.objects.count()
    total_categorias = Categoria.objects.count()
    total_emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).count()
    itens_estoque_baixo = Item.objects.filter(quantidade__lte=F('quantidade_minima')).count()
    
    # Itens com estoque mais baixo
    itens_criticos = Item.objects.filter(quantidade__lte=F('quantidade_minima')).order_by('quantidade')[:5]
    
    # Categorias com mais itens
    categorias_populares = Categoria.objects.annotate(
        total_itens=Count('itens')
    ).order_by('-total_itens')[:5]
    
    # Valor total do inventário
    valor_total = Item.objects.filter(valor_unitario__isnull=False).aggregate(
        total=Sum(F('quantidade') * F('valor_unitario'))
    )['total'] or 0
    
    # Empréstimos recentes
    emprestimos_recentes = Emprestimo.objects.all().order_by('-data_emprestimo')[:10]
    
    # Empréstimos em atraso
    emprestimos_atrasados = Emprestimo.objects.filter(
        data_devolucao__isnull=True, 
        data_prevista_devolucao__lt=timezone.now()
    ).order_by('data_prevista_devolucao')[:5]
    
    context = {
        'total_itens': total_itens,
        'total_categorias': total_categorias,
        'total_emprestimos_ativos': total_emprestimos_ativos,
        'itens_estoque_baixo': itens_estoque_baixo,
        'itens_criticos': itens_criticos,
        'categorias_populares': categorias_populares,
        'valor_total': valor_total,
        'emprestimos_recentes': emprestimos_recentes,
        'emprestimos_atrasados': emprestimos_atrasados,
    }
    return render(request, 'inventario/dashboard.html', context)

@staff_member_required
def item_list(request):
    """Lista todos os itens com paginação e filtros"""
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    mostrar_baixos = request.GET.get('baixos', False)
    
    itens = Item.objects.all()
    
    if query:
        itens = itens.filter(
            Q(nome__icontains=query) | 
            Q(codigo__icontains=query) | 
            Q(descricao__icontains=query)
        )
    
    if categoria_id:
        itens = itens.filter(categoria_id=categoria_id)
    
    if mostrar_baixos:
        itens = itens.filter(quantidade__lte=F('quantidade_minima'))
    
    # Ordenação
    order_by = request.GET.get('order_by', 'nome')
    itens = itens.order_by(order_by)
    
    # Paginação
    paginator = Paginator(itens, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id,
        'mostrar_baixos': mostrar_baixos,
        'order_by': order_by,
    }
    return render(request, 'inventario/item_list.html', context)

@staff_member_required
def item_detail(request, pk):
    """Visualização detalhada de um item específico"""
    item = get_object_or_404(Item, pk=pk)
    emprestimos = item.emprestimos.order_by('-data_emprestimo')[:10]  # Últimos 10 empréstimos
    
    context = {
        'item': item,
        'emprestimos': emprestimos,
    }
    return render(request, 'inventario/item_detail.html', context)

@staff_member_required
def item_create(request):
    """Adiciona um novo item ao inventário"""
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Item {item.nome} adicionado com sucesso!')
            return redirect('inventario:item_detail', pk=item.pk)
    else:
        form = ItemForm()
    
    context = {
        'form': form,
        'title': 'Adicionar Novo Item',
    }
    return render(request, 'inventario/item_form.html', context)

@staff_member_required
def item_update(request, pk):
    """Atualiza um item existente"""
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Item {item.nome} atualizado com sucesso!')
            return redirect('inventario:item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    
    context = {
        'form': form,
        'item': item,
        'title': 'Editar Item',
    }
    return render(request, 'inventario/item_form.html', context)

@staff_member_required
def item_delete(request, pk):
    """Remove um item do inventário"""
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        nome_item = item.nome
        item.delete()
        messages.success(request, f'Item {nome_item} removido com sucesso!')
        return redirect('inventario:item_list')
    
    context = {
        'item': item,
    }
    return render(request, 'inventario/item_confirm_delete.html', context)

@staff_member_required
def categoria_list(request):
    """Lista todas as categorias"""
    categorias = Categoria.objects.annotate(num_itens=Count('itens'))
    
    context = {
        'categorias': categorias,
    }
    return render(request, 'inventario/categoria_list.html', context)

@staff_member_required
def categoria_create(request):
    """Adiciona uma nova categoria"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria {categoria.nome} criada com sucesso!')
            return redirect('inventario:categoria_list')
    else:
        form = CategoriaForm()
    
    context = {
        'form': form,
        'title': 'Nova Categoria',
    }
    return render(request, 'inventario/categoria_form.html', context)

@staff_member_required
def emprestimo_list(request):
    """Lista todos os empréstimos"""
    status = request.GET.get('status', '')
    
    emprestimos = Emprestimo.objects.all()
    
    if status == 'ativos':
        emprestimos = emprestimos.filter(data_devolucao__isnull=True)
    elif status == 'atrasados':
        emprestimos = emprestimos.filter(
            data_devolucao__isnull=True, 
            data_prevista_devolucao__lt=timezone.now()
        )
    elif status == 'devolvidos':
        emprestimos = emprestimos.filter(data_devolucao__isnull=False)
    
    # Paginação
    paginator = Paginator(emprestimos.order_by('-data_emprestimo'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    return render(request, 'inventario/emprestimo_list.html', context)

@staff_member_required
def emprestimo_create(request):
    """Registra um novo empréstimo"""
    if request.method == 'POST':
        form = EmprestimoForm(request.POST)
        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.responsavel_emprestimo = request.user
            
            # Atualiza o estoque do item
            emprestimo.item.quantidade -= emprestimo.quantidade
            emprestimo.item.save()
            
            emprestimo.save()
            messages.success(request, f'Empréstimo de {emprestimo.item.nome} para {emprestimo.usuario.get_full_name()} registrado com sucesso!')
            return redirect('inventario:emprestimo_list')
    else:
        form = EmprestimoForm()
    
    context = {
        'form': form,
        'title': 'Novo Empréstimo',
    }
    return render(request, 'inventario/emprestimo_form.html', context)

@staff_member_required
def emprestimo_detail(request, pk):
    """Visualiza detalhes de um empréstimo"""
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    
    context = {
        'emprestimo': emprestimo,
    }
    return render(request, 'inventario/emprestimo_detail.html', context)

@staff_member_required
def emprestimo_devolucao(request, pk):
    """Registra a devolução de um item emprestado"""
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    
    if emprestimo.data_devolucao:
        messages.error(request, 'Este item já foi devolvido!')
        return redirect('inventario:emprestimo_detail', pk=emprestimo.pk)
    
    if request.method == 'POST':
        form = DevolucaoEmprestimoForm(request.POST)
        if form.is_valid():
            # Registra a devolução
            emprestimo.data_devolucao = timezone.now()
            emprestimo.responsavel_devolucao = request.user
            emprestimo.observacao = form.cleaned_data.get('observacao', emprestimo.observacao)
            
            # Devolve o item ao estoque
            emprestimo.item.quantidade += emprestimo.quantidade
            emprestimo.item.save()
            
            emprestimo.save()
            messages.success(request, f'Devolução de {emprestimo.item.nome} registrada com sucesso!')
            return redirect('inventario:emprestimo_list')
    else:
        form = DevolucaoEmprestimoForm()
    
    context = {
        'emprestimo': emprestimo,
        'form': form,
    }
    return render(request, 'inventario/emprestimo_devolucao_form.html', context)

@staff_member_required
def itens_criticos(request):
    """Atalho para visualizar apenas itens com estoque crítico"""
    return redirect(f"{reverse('inventario:item_list')}?baixos=true")
