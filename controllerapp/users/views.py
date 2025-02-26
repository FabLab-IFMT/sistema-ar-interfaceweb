from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from .models import CustomUser, Card
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def login_view(request): 
    if request.method == "POST": 
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid(): 
            login(request, form.get_user())
            return redirect("/")
    else: 
        form = CustomAuthenticationForm()
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

# Restrito a superusuários
def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, "users/user_list.html", {"users": users})
