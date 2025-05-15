from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Card, RegistrationRequest
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm, CustomPasswordChangeForm
from logs.utils import log_user_action
from django.http import Http404
from django.db import models
from projetos.models import Projeto
from canva.models import KanbanCard
from logs.models import Event
from options.models import Membro
from inventario.models import Emprestimo
from acesso_e_ponto.models import Session
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
import os

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

@login_required
def profile(request, user_id=None):
    # Se user_id for fornecido, exibe o perfil desse usuário
    # Se não, exibe o perfil do usuário logado
    if user_id and request.user.is_staff:
        profile_user = get_object_or_404(CustomUser, id=user_id)
        is_self = False
    else:
        profile_user = request.user
        is_self = True
        
    # Verifica se é um membro da equipe (usando o app options.Membro)
    is_team_member = False
    membro = None
    try:
        from options.models import Membro
        try:
            membro = Membro.objects.get(email=profile_user.email)
            is_team_member = True
        except Membro.DoesNotExist:
            pass
    except ImportError:
        pass
    
    # Busca projetos relacionados a este usuário
    projetos = []
    try:
        from projetos.models import Projeto
        projetos = Projeto.objects.filter(
            Q(responsavel=profile_user) | Q(participantes=profile_user)
        ).distinct()
    except ImportError:
        pass
    
    # Busca tarefas do kanban relacionadas a este usuário
    kanban_cards = []
    try:
        from canva.models import Card
        kanban_cards = Card.objects.filter(usuario_responsavel=profile_user)
    except ImportError:
        pass
    
    # Busca eventos agendados relacionados a este usuário
    eventos = []
    try:
        from logs.models import Event
        eventos = Event.objects.filter(
            Q(created_by=profile_user) | Q(participants=profile_user),
            start_time__gte=timezone.now()
        ).order_by('start_time')[:5]
    except ImportError:
        pass
    
    # Busca sessões de acesso recentes
    sessoes_recentes = []
    try:
        from acesso_e_ponto.models import Session
        sessoes_recentes = Session.objects.filter(
            user=profile_user
        ).order_by('-entry_time')[:5]
    except ImportError:
        pass
    
    # Busca empréstimos ativos (se for o próprio usuário ou admin)
    emprestimos_ativos = []
    if is_self or request.user.is_staff:
        try:
            from inventario.models import Emprestimo
            emprestimos_ativos = Emprestimo.objects.filter(
                usuario=profile_user,
                data_devolucao__isnull=True
            ).order_by('-data_emprestimo')
        except ImportError:
            pass
    
    # Se for o próprio usuário, mostra formulário de edição
    if is_self:
        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST, instance=profile_user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Seu perfil foi atualizado com sucesso.')
                return redirect('users:profile')
        else:
            form = ProfileUpdateForm(instance=profile_user)
    else:
        form = None
    
    context = {
        'profile_user': profile_user,
        'is_self': is_self,
        'is_team_member': is_team_member,
        'membro': membro,
        'form': form,
        'projetos': projetos,
        'kanban_cards': kanban_cards,
        'eventos': eventos,
        'sessoes_recentes': sessoes_recentes,
        'emprestimos_ativos': emprestimos_ativos,
    }
    
    return render(request, 'users/profile.html', context)

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = CustomUser.objects.filter(email=email)
            if users.exists():
                for user in users:
                    subject = "Solicitação de redefinição de senha"
                    email_template_name = "users/password_reset_email.html"
                    context = {
                        "email": user.email,
                        "domain": request.get_host(),
                        "site_name": "FabLab IFMT",
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": default_token_generator.make_token(user),
                        "protocol": "https" if request.is_secure() else "http",
                        "reset_url": f"{'https' if request.is_secure() else 'http'}://{request.get_host()}/users/password-reset-confirm/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/",
                    }
                    
                    # HTML do email
                    html_content = render_to_string(email_template_name, context)
                    # Versão texto plano para clientes de email que não suportam HTML
                    text_content = strip_tags(html_content)
                    
                    # Criando a mensagem com EmailMultiAlternatives
                    from_email = settings.DEFAULT_FROM_EMAIL
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.mixed_subtype = 'related'  # Importante para que as imagens embutidas funcionem
                    
                    # Caminho para a imagem da logo
                    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo_branco.png')
                    
                    # Anexar a imagem como uma incorporação
                    if os.path.exists(logo_path):
                        with open(logo_path, 'rb') as f:
                            logo_data = f.read()
                            logo_att = MIMEImage(logo_data)
                            logo_att.add_header('Content-ID', '<logo_branco.png>')
                            logo_att.add_header('Content-Disposition', 'inline', filename='logo_branco.png')
                            msg.attach(logo_att)
                            
                    try:
                        # Enviar o email
                        msg.send()
                    except BadHeaderError:
                        messages.error(request, "Ocorreu um erro ao enviar o email. Por favor, tente novamente mais tarde.")
                        return redirect("users:password_reset")
                    except Exception as e:
                        messages.error(request, f"Erro ao enviar email: {str(e)}. Por favor, tente novamente mais tarde.")
                        return redirect("users:password_reset")
                    
            # Sempre redirecionamos para a página de sucesso, mesmo se o email não existir
            # Isso evita que alguém descubra quais emails estão cadastrados
            return redirect("users:password_reset_done")
    else:
        form = PasswordResetForm()
    return render(request, "users/password_reset_form.html", {"form": form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantém o usuário logado
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})
