from django.shortcuts import render
from .models import Material

# Create your views here.

def equipamentos(request):
    materiais = Material.objects.all()
    return render(request, 'equipamentos.html', {'materiais': materiais})
