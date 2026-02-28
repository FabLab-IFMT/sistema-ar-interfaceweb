import logging
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from .models import Card, CustomUser, ProjectistRequest, Role
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm, CustomPasswordChangeForm
from logs.utils import log_user_action
from django.http import Http404
from django.db import models
from projetos.models import Projeto
from canva.models import KanbanCard
from logs.models import Event
from options.models import Membro
from inventario.models import Emprestimo
from acesso_e_ponto.models import Session, WeeklyRequiredHours
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
import os
import time
import threading


def send_confirmation_email_async(user: CustomUser, request):
    """Dispara email de confirmação em background com algumas tentativas de reenvio."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    confirm_link = request.build_absolute_uri(
        reverse("users:confirm_email", args=[uid, token])
    )

    subject = "Confirme seu email - FABLAB IFMT"
    html_body = render_to_string("users/email_confirm.html", {
        "user": user,
        "confirm_link": confirm_link,
    })
    text_body = strip_tags(html_body)

    def _send_email_async():
        for attempt in range(5):
            try:
                email = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
                email.attach_alternative(html_body, "text/html")
                email.send()
                return
            except Exception:
                logging.exception("Erro ao enviar email de confirmação (tentativa %s)", attempt + 1)
                time.sleep(0.4)

    threading.Thread(target=_send_email_async, daemon=True).start()

def login_view(request): 
    if request.method == "POST": 
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid(): 
            user = form.get_user()
            if not user.is_active or not getattr(user, "email_verified", True):
                # Reenvia email de confirmação se não estiver confirmado
                should_send = True
                session_key = f"confirm_retry_{user.pk}"
                last_sent = request.session.get(session_key)
                if last_sent and (time.time() - last_sent) < 30:
                    should_send = False
                if should_send:
                    send_confirmation_email_async(user, request)
                    request.session[session_key] = time.time()
                    messages.error(request, "Confirme seu email para acessar. Reenviamos o link; verifique também o spam.")
                else:
                    messages.error(request, "Confirme seu email para acessar. Já enviamos o link recentemente; verifique também o spam.")
            else:
                login(request, user)
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
            user: CustomUser = form.save(commit=False)
            user.is_active = False
            user.email_verified = False
            user.set_password(form.cleaned_data["password1"])
            user.save()

            send_confirmation_email_async(user, request)

            messages.info(
                request,
                "Estamos enviando o link de confirmação. Pode levar alguns minutos; verifique também o spam."
            )

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


def confirm_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        messages.success(request, "Email confirmado! Você já pode acessar o sistema.")
        return redirect('users:login')

    messages.error(request, "Link inválido ou expirado. Peça um novo cadastro.")
    return redirect('users:register')

def logout_view(request):
    if request.method == "POST":
        # Removido completamente o registro de log durante o logout
        logout(request)
        return redirect("/")
    return redirect("/")

# Restrito a superusuários ou gestores de projeto
def is_project_manager(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.has_role("gestor_projetos"))

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_project_manager)
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, "users/user_list.html", {"users": users})

@login_required
@user_passes_test(is_project_manager)
def pending_registrations(request):
    """Solicitações de título de projetista pendentes"""
    pending = ProjectistRequest.objects.filter(status='pending').select_related("user")
    return render(request, "users/autorizacao.html", {"pending_requests": pending})


@login_required
def request_projectist_title(request):
    if request.user.is_projectist():
        messages.info(request, "Você já é projetista.")
        return redirect('users:profile')

    existing_pending = ProjectistRequest.objects.filter(user=request.user, status='pending').first()
    if existing_pending:
        messages.info(request, "Sua solicitação de projetista já está pendente.")
        return redirect('users:profile')

    if request.method == 'POST':
        motivation = request.POST.get('motivation', '')
        ProjectistRequest.objects.create(user=request.user, motivation=motivation)
        messages.success(request, "Solicitação enviada! Um gestor irá analisar.")
        return redirect('users:profile')

    return render(request, 'users/request_projetista.html')

@login_required
@user_passes_test(is_project_manager)
def approve_registration(request, request_id):
    """Aprova solicitação de título de projetista"""
    if request.method == "POST":
        try:
            proj_req = ProjectistRequest.objects.select_related("user").get(id=request_id)

            if proj_req.status != 'pending':
                messages.error(request, f"Esta solicitação já foi {proj_req.get_status_display().lower()}.")
                return redirect('users:pending_registrations')

            proj_req.status = 'approved'
            proj_req.decided_at = timezone.now()
            proj_req.decided_by = request.user
            proj_req.save()

            role, _ = Role.objects.get_or_create(code="projetista", defaults={"name": "Projetista"})
            proj_req.user.roles.add(role)

            action = f"Aprovou projetista {proj_req.user.id}"
            description = f"Solicitação de projetista aprovada para {proj_req.user.first_name} {proj_req.user.last_name} ({proj_req.user.id})"
            log_user_action(request.user, action, description)

            messages.success(request, f"{proj_req.user.first_name} agora é projetista.")

        except ProjectistRequest.DoesNotExist:
            messages.error(request, "Solicitação não encontrada ou já processada.")

        return redirect('users:pending_registrations')

    return redirect('users:pending_registrations')

@login_required
@user_passes_test(is_project_manager)
def reject_registration(request, request_id):
    """Rejeita solicitação de título de projetista"""
    if request.method == "POST":
        try:
            proj_req = ProjectistRequest.objects.select_related("user").get(id=request_id)

            if proj_req.status != 'pending':
                messages.error(request, f"Esta solicitação já foi {proj_req.get_status_display().lower()}.")
                return redirect('users:pending_registrations')

            proj_req.status = 'rejected'
            proj_req.decided_at = timezone.now()
            proj_req.decided_by = request.user
            proj_req.save()

            action = f"Rejeitou projetista {proj_req.user.id}"
            description = f"Solicitação de projetista rejeitada para {proj_req.user.first_name} {proj_req.user.last_name} ({proj_req.user.id})"
            log_user_action(request.user, action, description)

            messages.success(request, f"Solicitação de {proj_req.user.first_name} {proj_req.user.last_name} foi rejeitada.")

        except ProjectistRequest.DoesNotExist:
            messages.error(request, "Solicitação não encontrada ou já processada.")

        return redirect('users:pending_registrations')

    return redirect('users:pending_registrations')


@login_required
@user_passes_test(is_superuser)
def manage_roles(request):
    roles = Role.objects.all().order_by('name')
    users = CustomUser.objects.all().prefetch_related('roles').order_by('first_name', 'last_name')

    if request.method == "POST":
        for user in users:
            selected_codes = request.POST.getlist(f"roles_{user.pk}")
            selected_roles = roles.filter(code__in=selected_codes)
            user.roles.set(selected_roles)

            has_staff_role = selected_roles.filter(is_staff_equivalent=True).exists()
            user.is_staff = user.is_superuser or has_staff_role
            user.save(update_fields=["is_staff"])

        messages.success(request, "Cargos atualizados com sucesso.")
        return redirect('users:manage_roles')

    return render(request, 'users/manage_roles.html', {"roles": roles, "users": users})

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
            logging.info("Perfil %s não corresponde a um Membro cadastrado", profile_user.email)
    except ImportError:
        logging.warning("App options.Membro não disponível para perfis")
    
    # Busca projetos relacionados a este usuário
    projetos = []
    try:
        from projetos.models import Projeto
        projetos = Projeto.objects.filter(
            Q(responsavel=profile_user) | Q(participantes=profile_user)
        ).distinct()
    except ImportError:
        logging.warning("App projetos.Projeto não disponível para perfis")
    
    # Busca tarefas do kanban relacionadas a este usuário
    kanban_cards = []
    try:
        from canva.models import Card
        kanban_cards = Card.objects.filter(usuario_responsavel=profile_user)
    except ImportError:
        logging.warning("App canva.Card não disponível para perfis")
    
    # Busca eventos agendados relacionados a este usuário
    eventos = []
    try:
        from logs.models import Event
        eventos = Event.objects.filter(
            Q(created_by=profile_user) | Q(participants=profile_user),
            start_time__gte=timezone.now()
        ).order_by('start_time')[:5]
    except ImportError:
        logging.warning("App logs.Event não disponível para perfis")
    
    # Busca sessões de acesso recentes e métricas de ponto
    sessoes_recentes = []
    week_hours = 0
    required_hours = 0
    progress_percent = 0
    time_remaining = 0
    active_session = None
    try:
        sessoes_recentes = Session.objects.filter(
            user=profile_user
        ).order_by('-entry_time')[:5]

        # Totais semanais (últimos 7 dias correntes)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        current_week_sessions = Session.objects.filter(
            user=profile_user,
            is_active=False,
            entry_time__date__gte=start_of_week,
        )

        for session in current_week_sessions:
            if session.duration:
                week_hours += session.duration.total_seconds() / 3600

        try:
            weekly_req = WeeklyRequiredHours.objects.get(user=profile_user)
            required_hours = weekly_req.required_hours
        except WeeklyRequiredHours.DoesNotExist:
            required_hours = 0

        if required_hours:
            progress_percent = min(100, int((week_hours / required_hours) * 100))
            time_remaining = max(0, required_hours - week_hours)
        else:
            progress_percent = 100
            time_remaining = 0

        active_session = Session.objects.filter(user=profile_user, is_active=True).first()
    except Exception as exc:
        logging.warning("Não foi possível calcular métricas de ponto: %s", exc)
    
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
            logging.warning("App inventario.Emprestimo não disponível para perfis")

    pending_projectist = None
    try:
        pending_projectist = ProjectistRequest.objects.filter(user=profile_user, status='pending').first()
    except Exception as exc:
        logging.warning("Não foi possível obter solicitações de projetista: %s", exc)

    projectist_status = "aprovado" if profile_user.is_projectist() else ("pendente" if pending_projectist else "disponivel")
    
    form = None
    if is_self:
        if request.method == 'POST':
            # Garante que uploads só de imagem continuem válidos preenchendo campos obrigatórios com os valores atuais
            data = request.POST.copy()
            if not data.get('first_name'):
                data['first_name'] = profile_user.first_name
            if not data.get('last_name'):
                data['last_name'] = profile_user.last_name
            if not data.get('email'):
                data['email'] = profile_user.email

            form = ProfileUpdateForm(data, request.FILES, instance=profile_user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Seu perfil foi atualizado com sucesso.')
                return redirect('users:profile')
        else:
            form = ProfileUpdateForm(instance=profile_user)
    
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
        'week_hours': week_hours,
        'required_hours': required_hours,
        'progress_percent': progress_percent,
        'time_remaining': time_remaining,
        'active_session': active_session,
        'pending_projectist': pending_projectist,
        'projectist_status': projectist_status,
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
