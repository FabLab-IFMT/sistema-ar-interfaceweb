from django.shortcuts import render
from .models import Material, Membro

# Create your views here.

def equipamentos(request):
    materiais = Material.objects.all()
    return render(request, 'equipamentos.html', {'materiais': materiais})

def membros(request):
    membros_ativos = Membro.objects.filter(ativo=True).order_by('ordem', 'nome')
    return render(request, 'membros.html', {'membros': membros_ativos})
