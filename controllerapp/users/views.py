from django.shortcuts import render
from django.http import HttpResponse

def login(request):
    return HttpResponse("pagina de login")

def register(request):
    return HttpResponse("pagina de registro")

def logout(request):
    return HttpResponse("pagina de logout")
