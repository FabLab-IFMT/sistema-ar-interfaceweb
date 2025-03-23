from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Material, Membro, CategoriaServico, Servico, SolicitacaoInteresse, Noticia, Hashtag
from .forms import SolicitacaoInteresseForm

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
    form = SolicitacaoInteresseForm(initial={'servico': servico})
    
    if request.method == 'POST':
        form = SolicitacaoInteresseForm(request.POST, request.FILES)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            if request.user.is_authenticated:
                solicitacao.usuario = request.user
            solicitacao.save()
            
            # Enviar email de notificação
            enviar_email_notificacao_interesse(solicitacao)
            
            messages.success(request, 'Sua solicitação de interesse foi registrada com sucesso! Entraremos em contato em breve.')
            return redirect('options:detalhe_servico', servico_id=servico.id)
    
    servicos_relacionados = Servico.objects.filter(categoria=servico.categoria, disponivel=True).exclude(id=servico.id)[:3]
    
    context = {
        'servico': servico,
        'form': form,
        'servicos_relacionados': servicos_relacionados
    }
    return render(request, 'detalhe_servico.html', context)

def enviar_email_notificacao_interesse(solicitacao):
    """Envia um email de notificação quando alguém demonstra interesse em uma capacidade."""
    assunto = f"Nova solicitação de interesse: {solicitacao.servico.nome}"
    
    # Criar conteúdo do email em HTML
    contexto = {
        'solicitacao': solicitacao,
        'servico': solicitacao.servico,
    }
    html_mensagem = render_to_string('emails/novo_interesse.html', contexto)
    
    # Texto simples para clientes de email que não suportam HTML
    texto_mensagem = f"""
    Nova solicitação de interesse no FabLab:
    
    Capacidade: {solicitacao.servico.nome}
    Nome: {solicitacao.nome}
    Email: {solicitacao.email}
    Telefone: {solicitacao.telefone or "Não informado"}
    
    Descrição do projeto/interesse:
    {solicitacao.descricao_projeto}
    
    ---
    Este é um email automático enviado pelo sistema do FabLab IFMT.
    """
    
    # Destinatário (email do administrador definido nas configurações)
    destinatario = settings.ADMIN_EMAIL
    
    # Email do remetente (definido nas configurações)
    remetente = settings.DEFAULT_FROM_EMAIL
    
    # Enviar o email
    try:
        send_mail(
            assunto,
            texto_mensagem,
            remetente,
            [destinatario],
            html_message=html_mensagem,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

@login_required
def minhas_solicitacoes(request):
    solicitacoes = SolicitacaoInteresse.objects.filter(usuario=request.user)
    return render(request, 'minhas_solicitacoes.html', {'solicitacoes': solicitacoes})

@login_required
def solicitacao_detalhe(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoInteresse, id=solicitacao_id)
    
    # Verificar se o usuário atual é o dono da solicitação ou é staff
    if request.user != solicitacao.usuario and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para visualizar esta solicitação.")
        return redirect('options:minhas_solicitacoes')
    
    return render(request, 'solicitacao_detalhe.html', {
        'solicitacao': solicitacao
    })

def noticias_lista(request):
    """View para listar todas as notícias publicadas."""
    noticias_lista = Noticia.objects.filter(publicado=True)
    
    # Buscar hashtags para exibir na sidebar
    todas_hashtags = Hashtag.objects.all()
    
    # Paginação - 10 notícias por página
    paginator = Paginator(noticias_lista, 9)  # 9 notícias por página (3x3)
    page = request.GET.get('page')
    noticias = paginator.get_page(page)
    
    return render(request, 'noticias.html', {
        'noticias': noticias,
        'hashtags': todas_hashtags,
        'titulo': 'Notícias e Comunicados'
    })

def noticias_por_tag(request, slug):
    """View para listar notícias filtradas por hashtag."""
    tag = get_object_or_404(Hashtag, slug=slug)
    noticias_lista = Noticia.objects.filter(publicado=True, hashtags=tag)
    
    # Buscar todas as hashtags para exibir na sidebar
    todas_hashtags = Hashtag.objects.all()
    
    # Paginação - 10 notícias por página
    paginator = Paginator(noticias_lista, 9)  # 9 notícias por página (3x3)
    page = request.GET.get('page')
    noticias = paginator.get_page(page)
    
    return render(request, 'noticias.html', {
        'noticias': noticias,
        'tag_atual': tag,
        'hashtags': todas_hashtags,
        'titulo': f'Notícias com tag #{tag.nome}'
    })

def noticia_detalhe(request, slug):
    """View para exibir uma notícia específica."""
    noticia = get_object_or_404(Noticia, slug=slug, publicado=True)
    
    # Buscar notícias relacionadas (mesma hashtag ou recentes)
    if noticia.hashtags.exists():
        # Se a notícia tem tags, buscamos outras com as mesmas tags
        tags = noticia.hashtags.all()
        noticias_relacionadas = Noticia.objects.filter(
            publicado=True,
            hashtags__in=tags
        ).exclude(id=noticia.id).distinct()[:3]
    else:
        # Se não tem tags, buscamos as mais recentes
        noticias_relacionadas = Noticia.objects.filter(
            publicado=True
        ).exclude(id=noticia.id)[:3]
    
    # Buscar todas as hashtags para sugestões
    todas_hashtags = Hashtag.objects.all()[:15]  # Limita a 15 tags para não sobrecarregar
    
    return render(request, 'noticia_detalhe.html', {
        'noticia': noticia,
        'noticias_relacionadas': noticias_relacionadas,
        'hashtags': todas_hashtags,
    })
