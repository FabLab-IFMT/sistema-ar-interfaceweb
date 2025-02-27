from django.shortcuts import render

def home(request):
    """View para a página inicial."""
    # Simplificada para evitar erros com o modelo CarouselImage
    return render(request, 'home.html')

def about(request):
    """View para a página sobre."""
    return render(request, 'about.html')

def projects(request):
    """View para a página de projetos."""
    return render(request, 'projects.html')