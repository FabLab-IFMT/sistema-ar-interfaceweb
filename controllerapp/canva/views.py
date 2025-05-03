from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, Http404
from django.db import models
from django.contrib.auth import get_user_model
import json
from .models import KanbanColumn, KanbanCard
from projetos.models import Projeto

User = get_user_model()

@login_required
def kanban_view(request):
    """Visualização principal do quadro Kanban"""
    # Superusuário vê todos os cards, usuários normais veem apenas seus cards
    colunas = KanbanColumn.objects.all()
    
    # Se não existir nenhuma coluna, criar as colunas padrão
    if not colunas.exists():
        colunas_padrao = [
            {'nome': 'A Fazer', 'ordem': 0, 'cor': '#f8f9fa'},
            {'nome': 'Em Andamento', 'ordem': 1, 'cor': '#fff3cd'},
            {'nome': 'Em Revisão', 'ordem': 2, 'cor': '#cff4fc'},
            {'nome': 'Concluído', 'ordem': 3, 'cor': '#d1e7dd'},
        ]
        for coluna_data in colunas_padrao:
            KanbanColumn.objects.create(**coluna_data)
        colunas = KanbanColumn.objects.all()
    
    # Determinar se deve mostrar cards ocultos
    mostrar_ocultos = request.GET.get('mostrar_ocultos') == '1'
    
    # Filtrar os cards que o usuário pode ver
    for coluna in colunas:
        cards_query = coluna.cards.filter(visivel=True) if not mostrar_ocultos else coluna.cards.all()
        
        if request.user.is_superuser:
            # Superusuário vê todos os cards (visíveis ou todos, dependendo do parâmetro)
            coluna.cards_filtrados = cards_query
        else:
            # Usuário comum vê apenas seus cards (como responsável ou membro)
            coluna.cards_filtrados = cards_query.filter(
                models.Q(responsavel=request.user) | models.Q(membros=request.user)
            ).distinct()
    
    # Obter projetos para o formulário de criação de cards
    if request.user.is_superuser:
        projetos = Projeto.objects.all()
    else:
        # Projetos onde o usuário é responsável ou participante
        projetos = Projeto.objects.filter(
            models.Q(responsavel=request.user) | models.Q(participantes=request.user)
        ).distinct()
    
    # Obter usuários para filtro e seleções
    usuarios = None
    if request.user.is_superuser:
        usuarios = User.objects.filter(is_active=True)
    
    return render(request, 'cambam/cambam.html', {
        'colunas': colunas,
        'projetos': projetos,
        'usuarios': usuarios,
    })

@login_required
def add_card(request):
    """Adiciona um novo card ao quadro"""
    if request.method == 'POST':
        data = json.loads(request.body)
        titulo = data.get('titulo')
        descricao = data.get('descricao')
        coluna_id = data.get('coluna')
        projeto_id = data.get('projeto')
        prioridade = data.get('prioridade')
        
        if not titulo or not coluna_id:
            return JsonResponse({'status': 'error', 'message': 'Título e coluna são obrigatórios'})
        
        try:
            coluna = KanbanColumn.objects.get(id=coluna_id)
            projeto = None
            if projeto_id:
                projeto = Projeto.objects.get(id=projeto_id)
                
            # Verificar permissão para projetos
            if projeto and not request.user.is_superuser:
                if request.user != projeto.responsavel and request.user not in projeto.participantes.all():
                    return JsonResponse({'status': 'error', 'message': 'Você não tem permissão para este projeto'})
                
            # Criar o card
            card = KanbanCard.objects.create(
                titulo=titulo,
                descricao=descricao,
                coluna=coluna,
                projeto=projeto,
                responsavel=request.user,
                prioridade=prioridade,
                criado_por=request.user,
                ordem=KanbanCard.objects.filter(coluna=coluna).count()
            )
            
            # Se houver membros no request, adicionar ao card
            membros_ids = data.get('membros', [])
            if membros_ids:
                membros = User.objects.filter(id__in=membros_ids)
                card.membros.add(*membros)
            
            return JsonResponse({
                'status': 'success',
                'card': {
                    'id': card.id,
                    'titulo': card.titulo,
                    'responsavel': card.responsavel.first_name if card.responsavel else '',
                    'prioridade': card.get_prioridade_display(),
                    'projeto': card.projeto.titulo if card.projeto else '',
                }
            })
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@login_required
def move_card(request):
    """Atualiza a posição de um card"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            coluna_id = data.get('coluna_id')
            nova_ordem = data.get('ordem')
            
            if not card_id or not coluna_id:
                return JsonResponse({'status': 'error', 'message': 'ID do card e da coluna são obrigatórios'})
                
            try:
                card = KanbanCard.objects.get(id=card_id)
                coluna = KanbanColumn.objects.get(id=coluna_id)
            except (KanbanCard.DoesNotExist, KanbanColumn.DoesNotExist):
                return JsonResponse({'status': 'error', 'message': 'Card ou coluna não encontrados'})
            
            # Agora também permite que membros do card o movam
            is_member = request.user in card.membros.all()
            can_move = (request.user.is_superuser or 
                      request.user == card.responsavel or 
                      request.user == card.criado_por or
                      is_member)
                      
            if not can_move:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Você não tem permissão para mover este card'
                }, status=403)
            
            # Atualizar coluna e ordem
            old_coluna = card.coluna
            card.coluna = coluna
            card.ordem = nova_ordem
            card.save()
            
            # Reordenar cards na coluna antiga e na nova
            reordenar_cards_apos_movimento(old_coluna)
            if old_coluna.id != coluna.id:
                reordenar_cards_apos_movimento(coluna)
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Dados inválidos'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

def reordenar_cards_apos_movimento(coluna):
    """Reordena os cards após adição/remoção de um card"""
    cards = coluna.cards.all().order_by('ordem')
    for i, card in enumerate(cards):
        if card.ordem != i:
            card.ordem = i
            card.save(update_fields=['ordem'])

@login_required
def card_details(request, card_id):
    """Exibe ou atualiza detalhes de um card"""
    try:
        card = get_object_or_404(KanbanCard, id=card_id)
        
        # Verificar permissão - qualquer um dos seguintes pode ver o card:
        # 1. Superusuário
        # 2. Responsável pelo card
        # 3. Membro do card
        # 4. Criador do card
        is_member = request.user in card.membros.all()
        can_view = (request.user.is_superuser or 
                   request.user == card.responsavel or 
                   is_member or
                   request.user == card.criado_por)
                   
        if not can_view:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Você não tem permissão para ver este card'
                }, status=403)
            else:
                raise Http404("Card não encontrado")
        
        if request.method == 'GET':
            # Determina se o usuário pode editar o card
            can_edit = (request.user.is_superuser or 
                       request.user == card.responsavel or 
                       request.user == card.criado_por)
                       
            context = {
                'card': card,
                'can_edit': can_edit
            }
            
            # Adiciona usuários apenas para quem pode editar
            if can_edit:
                context['usuarios'] = User.objects.filter(is_active=True)
                
            return render(request, 'cambam/card_details.html', context)
        
        elif request.method == 'POST':
            # Verificar permissão para edição
            can_edit = (request.user.is_superuser or 
                       request.user == card.responsavel or 
                       request.user == card.criado_por)
                       
            if not can_edit:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Você não tem permissão para editar este card'
                }, status=403)
            
            try:
                data = json.loads(request.body)
                
                # Atualizações básicas permitidas
                card.titulo = data.get('titulo', card.titulo)
                card.descricao = data.get('descricao', card.descricao)
                card.prioridade = data.get('prioridade', card.prioridade)
                
                # Atualizar visibilidade
                visivel = data.get('visivel')
                if visivel is not None:
                    card.visivel = visivel == True or visivel == 'true' or visivel == '1'
                
                # Atualizações adicionais (apenas para superusers ou responsável)
                if request.user.is_superuser or request.user == card.responsavel:
                    # Atualizar responsável
                    responsavel_id = data.get('responsavel_id')
                    if responsavel_id:
                        try:
                            novo_responsavel = User.objects.get(id=responsavel_id)
                            card.responsavel = novo_responsavel
                        except User.DoesNotExist:
                            pass
                    elif responsavel_id == '':
                        card.responsavel = None
                    
                    # Atualizar membros
                    membros_ids = data.get('membros_ids', [])
                    if membros_ids is not None:
                        card.membros.clear()
                        membros = User.objects.filter(id__in=membros_ids)
                        card.membros.add(*membros)
                
                card.save()
                return JsonResponse({'status': 'success'})
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Dados inválidos'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erro: {str(e)}'}, status=500)

@login_required
def delete_card(request, card_id):
    """Remove um card do quadro"""
    if request.method == 'POST':
        try:
            card = get_object_or_404(KanbanCard, id=card_id)
            
            # Verificar permissão
            if not request.user.is_superuser and request.user != card.criado_por:
                return JsonResponse({'status': 'error', 'message': 'Sem permissão para excluir'})
            
            card.delete()
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método inválido'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_column(request):
    """Adiciona uma nova coluna ao quadro (apenas superusuário)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        nome = data.get('nome')
        cor = data.get('cor', '#f8f9fa')
        
        if not nome:
            return JsonResponse({'status': 'error', 'message': 'Nome da coluna é obrigatório'})
        
        # Obter a maior ordem existente e incrementar
        ultima_ordem = KanbanColumn.objects.all().aggregate(models.Max('ordem'))['ordem__max'] or -1
        
        coluna = KanbanColumn.objects.create(
            nome=nome,
            cor=cor,
            ordem=ultima_ordem + 1
        )
        
        return JsonResponse({
            'status': 'success',
            'coluna': {
                'id': coluna.id,
                'nome': coluna.nome,
                'cor': coluna.cor
            }
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_column(request, column_id):
    """Remove uma coluna do quadro (apenas superusuário)"""
    if request.method == 'POST':
        try:
            coluna = get_object_or_404(KanbanColumn, id=column_id)
            
            # Verificar se a coluna tem cards
            if coluna.cards.exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Esta coluna contém cards. Mova-os para outra coluna antes de excluir.'
                })
                
            coluna.delete()
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método inválido'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reorder_columns(request):
    """Reordena as colunas do quadro (apenas superusuário)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            colunas_ordem = data.get('colunas', [])
            
            for ordem_info in colunas_ordem:
                coluna_id = ordem_info.get('id')
                nova_ordem = ordem_info.get('ordem')
                
                if coluna_id and nova_ordem is not None:
                    coluna = KanbanColumn.objects.get(id=coluna_id)
                    coluna.ordem = nova_ordem
                    coluna.save()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método inválido'})

# Adiciona nova função para editar coluna
@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_column(request, column_id):
    """Edita uma coluna existente (apenas superusuário)"""
    if request.method == 'POST':
        try:
            coluna = get_object_or_404(KanbanColumn, id=column_id)
            data = json.loads(request.body)
            
            # Atualizar dados da coluna
            coluna.nome = data.get('nome', coluna.nome)
            coluna.cor = data.get('cor', coluna.cor)
            coluna.save()
            
            return JsonResponse({
                'status': 'success',
                'coluna': {
                    'id': coluna.id,
                    'nome': coluna.nome,
                    'cor': coluna.cor
                }
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})
