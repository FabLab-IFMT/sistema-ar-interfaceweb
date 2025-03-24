from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import CustomUser, Card
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from logs.utils import log_user_action

def login_view(request): 
    if request.method == "POST": 
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid(): 
            login(request, form.get_user())
            messages.success(request, f"Bem-vindo de volta!")
            return redirect("/")
        else:
            messages.error(request, "Matrícula ou senha incorretos. Por favor, tente novamente.")
    else: 
        form = CustomAuthenticationForm()
    return render(request, "users/login.html", { "form": form })

def register_view(request):
    if request.method == "POST": 
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Conta criada com sucesso! Bem-vindo, {user.first_name}!")
            return redirect("/")
        else:
            # Mensagens de erro específicas para campos únicos
            if 'email' in form.errors:
                messages.error(request, "Este email já está cadastrado no sistema.")
            if 'id' in form.errors:
                messages.error(request, "Este número de matrícula já está cadastrado no sistema.")
            
            # Exibir também erros de senha e outros campos
            for field, errors in form.errors.items():
                for error in errors:
                    if field not in ['email', 'id']:
                        messages.error(request, f"{error}")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", { "form": form })

def logout_view(request):
    if request.method == "POST":
        # Removendo completamente o registro de log no logout
        # para evitar problemas com o campo author
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
