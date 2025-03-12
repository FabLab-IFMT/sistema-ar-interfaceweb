from django.shortcuts import render

# Removed duplicate function definition of home

def about(request):
    """View para a página sobre."""
    return render(request, 'about.html')

def projects(request):
    """View para a página de projetos."""
    return render(request, 'projects.html')

# Importe o modelo CarouselImage
from Controle_ar.models import CarouselImage

def home(request):
    # Busca apenas imagens ativas do carrossel
    carousel_images = CarouselImage.objects.filter(active=True)
    
    # Para depuração
    debug = request.GET.get('debug', False)
    
    context = {
        'carousel_images': carousel_images,
        'debug': debug,
        # Outras variáveis de contexto que possam existir...
    }
    
    return render(request, 'home.html', context)
