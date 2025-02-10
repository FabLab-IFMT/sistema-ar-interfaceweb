from django.shortcuts import render

# Create your views here.

def equipamentos(request):
    return render(request, 'equipamentos.html')
