from django.http import HttpResponse
from django.shortcuts import render
from Controle_ar.models import CarouselImage

def homepage(request):
    carousel_images = CarouselImage.objects.filter(active=True)
    return render(request, 'home.html', {'carousel_images': carousel_images})

def about(request):
    return render(request, "about.html")

def projects(request):
    return render(request, "project.html")