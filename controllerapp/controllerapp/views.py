from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

# Removed duplicate function definition of home

def toggle_theme(request):
    """View para alternar entre tema claro e escuro."""
    # Obtém o tema atual do cookie ou define como 'light' se não existir
    current_theme = request.COOKIES.get('theme', 'light')
    
    # Alterna entre 'light' e 'dark'
    new_theme = 'dark' if current_theme == 'light' else 'light'
    
    # Redireciona para a página anterior ou para a página inicial
    response = redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # Define o cookie com o novo tema (validade de 365 dias)
    response.set_cookie('theme', new_theme, max_age=365*24*60*60)
    
    return response

def get_theme(request):
    """Função auxiliar para obter o tema atual do usuário."""
    return request.COOKIES.get('theme', 'light')

def about(request):
    """View para a página sobre."""
    theme = get_theme(request)
    return render(request, 'about.html', {'theme': theme})

def projects(request):
    """View para a página de projetos."""
    theme = get_theme(request)
    return render(request, 'projects.html', {'theme': theme})

# Importe o modelo CarouselImage e o novo modelo Noticia
from Controle_ar.models import CarouselImage
from options.models import Noticia
# Nova importação para os eventos
from logs.models import Event

def home(request):
    # Busca apenas imagens ativas do carrossel
    carousel_images = CarouselImage.objects.filter(active=True)
    
    # Busca notícias marcadas para exibir na página inicial
    noticias_home = Noticia.objects.filter(publicado=True, mostrar_na_home=True)[:3]
    
    # Buscar próximos eventos (apenas aprovados e futuros)
    now = timezone.now()
    proximos_eventos = Event.objects.filter(
        approved=True,
        start_time__gte=now,
        # Filtramos apenas os tipos de eventos que queremos mostrar
        event_type__in=['internal', 'workshop', 'maintenance']
    ).order_by('start_time')[:5]  # Limitar aos próximos 5 eventos
    
    # Para depuração
    debug = request.GET.get('debug', False)
    
    # Obtém o tema atual
    theme = get_theme(request)
    
    context = {
        'carousel_images': carousel_images,
        'noticias': noticias_home,
        'tem_noticias': noticias_home.exists(),  # Para verificar se há notícias
        'proximos_eventos': proximos_eventos,
        'tem_eventos': proximos_eventos.exists(),
        'debug': debug,
        'theme': theme,
        # Outras variáveis de contexto que possam existir...
    }
    
    return render(request, 'home.html', context)

# Handlers de erros personalizados - modificados para funcionarem com URLs de teste
def bad_request(request, exception=None):
    """View para erro 400 - Bad Request"""
    theme = get_theme(request)
    return render(request, 'errors/400.html', {'theme': theme}, status=400)

def permission_denied(request, exception=None):
    """View para erro 403 - Forbidden"""
    theme = get_theme(request)
    return render(request, 'errors/403.html', {'theme': theme}, status=403)

def page_not_found(request, exception=None):
    """View para erro 404 - Page Not Found"""
    theme = get_theme(request)
    return render(request, 'errors/404.html', {'theme': theme}, status=404)

def server_error(request, exception=None):
    """View para erro 500 - Server Error - modificado para aceitar exception"""
    theme = get_theme(request)
    return render(request, 'errors/500.html', {'theme': theme}, status=500)
