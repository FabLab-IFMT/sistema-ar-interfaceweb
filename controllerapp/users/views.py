from django.shortcuts import render, redirect, HttpResponse 
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm 
from .forms import CustomUserCreationForm
from django.contrib.auth import login, logout


def login_view(request): 
    if request.method == "POST": 
        form = AuthenticationForm(data=request.POST)
        if form.is_valid(): 
            login(request, form.get_user())
            return redirect("/")
    else: 
        form = AuthenticationForm()
    return render(request, "users/login.html", { "form": form })

def register_view(request):
    if request.method == "POST": 
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid():
            login(request, form.save())
            return redirect("/")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", { "form": form })

def logout_view(request):
    if request.method == "POST": 
        logout(request) 
        return redirect("/")
    return redirect("/")

