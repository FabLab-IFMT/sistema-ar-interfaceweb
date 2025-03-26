from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Card, RegistrationRequest
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from logs.utils import log_user_action
from django.http import Http404

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
            # Ao invés de criar o usuário, salvamos a solicitação de registro
            registration_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'id_number': form.cleaned_data['id'],
                'password': make_password(form.cleaned_data['password1'])
            }
            
            # Verificar se já existe um usuário com este email ou matrícula
            if CustomUser.objects.filter(email=registration_data['email']).exists():
                messages.error(request, "Este email já está cadastrado no sistema.")
                return render(request, "users/register.html", {"form": form})
            
            if CustomUser.objects.filter(id=registration_data['id_number']).exists():
                messages.error(request, "Este número de matrícula já está cadastrado no sistema.")
                return render(request, "users/register.html", {"form": form})
                
            # Verificar se já existe uma solicitação pendente com este email ou matrícula
            if RegistrationRequest.objects.filter(email=registration_data['email'], status='pending').exists():
                messages.error(request, "Já existe uma solicitação pendente com este email.")
                return render(request, "users/register.html", {"form": form})
                
            if RegistrationRequest.objects.filter(id_number=registration_data['id_number'], status='pending').exists():
                messages.error(request, "Já existe uma solicitação pendente com esta matrícula.")
                return render(request, "users/register.html", {"form": form})
                
            # Criar solicitação de registro
            RegistrationRequest.objects.create(**registration_data)
            messages.success(request, "Sua solicitação de registro foi enviada! Um administrador irá revisar seus dados em breve.")
            return redirect("/users/login/")
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
        # Removido completamente o registro de log durante o logout
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

@login_required
@user_passes_test(is_superuser)
def pending_registrations(request):
    """View para exibir solicitações de registro pendentes"""
    pending = RegistrationRequest.objects.filter(status='pending')
    return render(request, "users/autorizacao.html", {"pending_requests": pending})

@login_required
@user_passes_test(is_superuser)
def approve_registration(request, request_id):
    """View para aprovar uma solicitação de registro"""
    if request.method == "POST":
        try:
            # Use try/except para lidar com o caso em que a solicitação não exista
            reg_request = RegistrationRequest.objects.get(id=request_id)
            
            # Verificar se a solicitação já foi processada
            if reg_request.status != 'pending':
                messages.error(request, f"Esta solicitação já foi {reg_request.get_status_display().lower()}.")
                return redirect('users:pending_registrations')
                
            # Criar o novo usuário
            user = CustomUser.objects.create(
                id=reg_request.id_number,
                email=reg_request.email,
                first_name=reg_request.first_name,
                last_name=reg_request.last_name,
                password=reg_request.password  # Já está com hash
            )
            
            # Atualizar o status da solicitação
            reg_request.status = 'approved'
            reg_request.save()
            
            # Registrar a ação
            action = f"Aprovou o registro do usuário {user.id}"
            description = f"O administrador aprovou a solicitação de registro do usuário {user.first_name} {user.last_name} ({user.id})"
            log_user_action(request.user, action, description)
            
            messages.success(request, f"Usuário {user.first_name} {user.last_name} aprovado com sucesso!")
            
        except RegistrationRequest.DoesNotExist:
            messages.error(request, "A solicitação de registro não foi encontrada ou já foi processada.")
            
        return redirect('users:pending_registrations')
    
    return redirect('users:pending_registrations')

@login_required
@user_passes_test(is_superuser)
def reject_registration(request, request_id):
    """View para rejeitar uma solicitação de registro"""
    if request.method == "POST":
        try:
            # Use try/except para lidar com o caso em que a solicitação não exista
            reg_request = RegistrationRequest.objects.get(id=request_id)
            
            # Verificar se a solicitação já foi processada
            if reg_request.status != 'pending':
                messages.error(request, f"Esta solicitação já foi {reg_request.get_status_display().lower()}.")
                return redirect('users:pending_registrations')
            
            # Atualizar o status da solicitação
            reg_request.status = 'rejected'
            reg_request.save()
            
            # Registrar a ação
            action = f"Rejeitou o registro da solicitação {reg_request.id_number}"
            description = f"O administrador rejeitou a solicitação de registro de {reg_request.first_name} {reg_request.last_name} ({reg_request.id_number})"
            log_user_action(request.user, action, description)
            
            messages.success(request, f"Solicitação de {reg_request.first_name} {reg_request.last_name} rejeitada!")
            
        except RegistrationRequest.DoesNotExist:
            messages.error(request, "A solicitação de registro não foi encontrada ou já foi processada.")
            
        return redirect('users:pending_registrations')
    
    return redirect('users:pending_registrations')

# Podemos remover esta função já que usamos o context processor agora
# def get_pending_count():
#     """Função auxiliar para contar solicitações pendentes"""
#     return RegistrationRequest.objects.filter(status='pending').count()
