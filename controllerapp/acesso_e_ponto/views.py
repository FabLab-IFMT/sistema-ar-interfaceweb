from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields, Q
from django.db.models.functions import ExtractWeek, ExtractYear
import json
from datetime import datetime, timedelta

from users.models import Card, CustomUser
from .models import TimeLog, Session, WeeklyRequiredHours

# Função auxiliar para verificação de permissão
def is_staff(user):
    return user.is_staff

@csrf_exempt  # Desativa proteção CSRF para permitir requisições do ESP32
def check_card(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Lendo JSON enviado pelo ESP32
            card_number = data.get("card_number")

            if not card_number:
                return JsonResponse({"message": "Número do cartão não enviado"}, status=400)

            # Verifica se o cartão existe no banco de dados
            try:
                card = Card.objects.get(card_number=card_number)
                user = card.user
                
                # Verificar se usuário já está no laboratório (sessão ativa)
                active_session = Session.objects.filter(user=user, is_active=True).first()
                
                if active_session:
                    # Registrar saída
                    TimeLog.objects.create(
                        user=user, 
                        status='saida',
                        registered_by_card=card_number
                    )
                    active_session.close_session()
                    
                    # Calcular duração desta sessão
                    duration = active_session.duration
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    
                    return JsonResponse({
                        "authorized": True, 
                        "message": f"Saída registrada",
                        "action": "exit",
                        "user_name": f"{user.first_name} {user.last_name}",
                        "session_time": f"{hours}h {minutes}min",
                        "display_message": f"Tchau, {user.first_name}! Tempo: {hours}h {minutes}min"
                    })
                else:
                    # Registrar entrada
                    TimeLog.objects.create(
                        user=user, 
                        status='entrada',
                        registered_by_card=card_number
                    )
                    Session.objects.create(
                        user=user,
                        entry_time=timezone.now()
                    )
                    
                    # Verificar requisito de horas semanais
                    try:
                        weekly_req = WeeklyRequiredHours.objects.get(user=user)
                        required_hours = weekly_req.required_hours
                    except WeeklyRequiredHours.DoesNotExist:
                        required_hours = 0
                    
                    # Calcular horas já cumpridas na semana
                    today = timezone.now().date()
                    start_of_week = today - timedelta(days=today.weekday())
                    week_sessions = Session.objects.filter(
                        user=user,
                        is_active=False,
                        entry_time__gte=start_of_week
                    )
                    
                    week_hours = 0
                    for session in week_sessions:
                        if session.duration:
                            week_hours += session.duration.total_seconds() / 3600
                    
                    remaining_hours = max(0, required_hours - week_hours)
                    
                    return JsonResponse({
                        "authorized": True, 
                        "message": f"Entrada registrada",
                        "action": "entry",
                        "user_name": f"{user.first_name} {user.last_name}",
                        "week_hours": f"{week_hours:.1f}h de {required_hours}h",
                        "remaining_hours": f"{remaining_hours:.1f}h restantes",
                        "display_message": f"Bem-vindo, {user.first_name}! Falta: {remaining_hours:.1f}h"
                    })
                
            except Card.DoesNotExist:
                return JsonResponse({
                    "authorized": False, 
                    "message": "Cartão não cadastrado",
                    "display_message": "Acesso Negado! Cartao invalido."
                })

        except json.JSONDecodeError:
            return JsonResponse({"message": "Erro ao processar JSON"}, status=400)
    
    return JsonResponse({"message": "Método não permitido"}, status=405)

@csrf_exempt
def check_card_status(request):
    """Endpoint para verificar o status atual de um cartão (entrada/saída)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_number = data.get("card_number")

            if not card_number:
                return JsonResponse({"message": "Número do cartão não enviado"}, status=400)

            try:
                card = Card.objects.get(card_number=card_number)
                user = card.user
                
                # Verifica se há sessão ativa
                active_session = Session.objects.filter(user=user, is_active=True).first()
                
                if active_session:
                    duration = active_session.calculate_duration()
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    
                    return JsonResponse({
                        "status": "active",
                        "user_name": f"{user.first_name} {user.last_name}",
                        "entry_time": active_session.entry_time.strftime("%H:%M"),
                        "current_duration": f"{hours}h {minutes}min",
                        "display_message": f"{user.first_name} presente ha {hours}h {minutes}min"
                    })
                else:
                    last_session = Session.objects.filter(user=user, is_active=False).first()
                    if last_session and last_session.exit_time:
                        last_exit = last_session.exit_time.strftime("%d/%m %H:%M")
                        return JsonResponse({
                            "status": "inactive",
                            "user_name": f"{user.first_name} {user.last_name}",
                            "last_exit": last_exit,
                            "display_message": f"{user.first_name} saiu em {last_exit}"
                        })
                    else:
                        return JsonResponse({
                            "status": "inactive",
                            "user_name": f"{user.first_name} {user.last_name}",
                            "display_message": f"{user.first_name} ausente"
                        })
            
            except Card.DoesNotExist:
                return JsonResponse({
                    "status": "unknown",
                    "message": "Cartão não cadastrado",
                    "display_message": "Cartao nao cadastrado"
                })
                
        except json.JSONDecodeError:
            return JsonResponse({"message": "Erro ao processar JSON"}, status=400)
    
    return JsonResponse({"message": "Método não permitido"}, status=405)

@login_required
@user_passes_test(is_staff)
def my_access_history(request):
    """Exibe o histórico de acessos do usuário logado (apenas staff)"""
    user = request.user
    
    # Obter sessões dos últimos 30 dias
    last_30_days = timezone.now() - timedelta(days=30)
    sessions = Session.objects.filter(user=user, entry_time__gte=last_30_days).order_by('-entry_time')
    
    # Calcular totais por semana
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    current_week_sessions = Session.objects.filter(
        user=user,
        is_active=False,
        entry_time__gte=start_of_week
    )
    
    # Horas desta semana
    week_hours = 0
    for session in current_week_sessions:
        if session.duration:
            week_hours += session.duration.total_seconds() / 3600
    
    # Obter requisito de horas semanais
    try:
        weekly_req = WeeklyRequiredHours.objects.get(user=user)
        required_hours = weekly_req.required_hours
    except WeeklyRequiredHours.DoesNotExist:
        required_hours = 0
    
    # Verificar se há sessão ativa
    active_session = Session.objects.filter(user=user, is_active=True).first()
    
    context = {
        'sessions': sessions,
        'week_hours': week_hours,
        'required_hours': required_hours,
        'active_session': active_session,
        'time_remaining': max(0, required_hours - week_hours),
        'progress_percent': min(100, int((week_hours / required_hours * 100) if required_hours else 100)),
    }
    
    return render(request, 'acesso_e_ponto/my_access_history.html', context)

@login_required
@user_passes_test(is_staff)
def user_access_history(request, user_id):
    """Visualização de histórico de outro usuário (apenas para staff)"""
    if not request.user.is_staff:
        return redirect('acesso_e_ponto:my_access_history')
    
    user = get_object_or_404(CustomUser, pk=user_id)
    
    # Obter sessões dos últimos 30 dias
    last_30_days = timezone.now() - timedelta(days=30)
    sessions = Session.objects.filter(user=user, entry_time__gte=last_30_days).order_by('-entry_time')
    
    # Calcular totais por semana
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    current_week_sessions = Session.objects.filter(
        user=user,
        is_active=False,
        entry_time__gte=start_of_week
    )
    
    # Horas desta semana
    week_hours = 0
    for session in current_week_sessions:
        if session.duration:
            week_hours += session.duration.total_seconds() / 3600
    
    # Obter requisito de horas semanais
    try:
        weekly_req = WeeklyRequiredHours.objects.get(user=user)
        required_hours = weekly_req.required_hours
    except WeeklyRequiredHours.DoesNotExist:
        required_hours = 0
    
    # Verificar se há sessão ativa
    active_session = Session.objects.filter(user=user, is_active=True).first()
    
    context = {
        'target_user': user,
        'sessions': sessions,
        'week_hours': week_hours,
        'required_hours': required_hours,
        'active_session': active_session,
        'time_remaining': max(0, required_hours - week_hours),
        'progress_percent': min(100, int((week_hours / required_hours * 100) if required_hours else 100)),
    }
    
    return render(request, 'acesso_e_ponto/user_access_history.html', context)

@login_required
@user_passes_test(is_staff)
def dashboard(request):
    """Dashboard do sistema de ponto - mostra dados variados dependendo do tipo de usuário (apenas staff)"""
    # Configurar datas para cálculos
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Para todos os usuários com is_staff:
    # Usuários atualmente presentes
    active_sessions = Session.objects.filter(is_active=True).select_related('user')
    
    # Estatísticas gerais
    today_sessions = Session.objects.filter(
        entry_time__date=today
    ).count()
    
    # Total de horas registradas esta semana
    week_sessions = Session.objects.filter(
        entry_time__gte=start_of_week,
        is_active=False
    )
    
    total_hours = 0
    for session in week_sessions:
        if session.duration:
            total_hours += session.duration.total_seconds() / 3600
    
    # Usuários com carga horária
    users_with_req = WeeklyRequiredHours.objects.all().select_related('user')
    users_status = []
    
    for user_req in users_with_req:
        user_week_sessions = Session.objects.filter(
            user=user_req.user,
            is_active=False,
            entry_time__gte=start_of_week
        )
        
        user_hours = 0
        for session in user_week_sessions:
            if session.duration:
                user_hours += session.duration.total_seconds() / 3600
        
        is_active = Session.objects.filter(user=user_req.user, is_active=True).exists()
        
        users_status.append({
            'user': user_req.user,
            'required': user_req.required_hours,
            'completed': user_hours,
            'percentage': min(100, int((user_hours / user_req.required_hours * 100) if user_req.required_hours else 100)),
            'is_active': is_active
        })
    
    context = {
        'active_sessions': active_sessions,
        'today_sessions': today_sessions,
        'total_hours': total_hours,
        'users_status': users_status,
        'is_superuser': request.user.is_superuser,  # Para controle na template
    }
    
    return render(request, 'acesso_e_ponto/dashboard.html', context)
