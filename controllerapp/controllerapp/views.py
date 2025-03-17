from django.shortcuts import render, redirect
from django.http import HttpResponse

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

# Importe o modelo CarouselImage
from Controle_ar.models import CarouselImage

def home(request):
    # Busca apenas imagens ativas do carrossel
    carousel_images = CarouselImage.objects.filter(active=True)
    
    # Para depuração
    debug = request.GET.get('debug', False)
    
    # Obtém o tema atual
    theme = get_theme(request)
    
    context = {
        'carousel_images': carousel_images,
        'debug': debug,
        'theme': theme,
        # Outras variáveis de contexto que possam existir...
    }
    
    return render(request, 'home.html', context)
