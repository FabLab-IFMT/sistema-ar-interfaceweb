from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta, date
import calendar
from .models import Action, Event, LabSchedule
from .scripts import FormattedAction
from .forms import EventForm, VisitRequestForm
from Email_notificacoes.models import enviar_email_solicitacao_enviada, enviar_email_solicitacao_aprovada

def staff_check(user):
    return user.is_staff

# Views para logs (acesso apenas para staff)
@user_passes_test(staff_check)
def logs_list(request):
    dates = []

    for action in Action.objects.all():
        if action.date not in dates:
            dates.append(action.date)

    return render(request, 'logs/logs_list.html', {'dates': dates})

@user_passes_test(staff_check)
def logs_datepage(request, day, month, year):
    actions = [FormattedAction(action) for action in Action.objects.all().order_by('time') if action.date == date(year, month, day)]    
    current_date = date(year, month, day)

    return render(request, 'logs/logs_datepage.html', {'actions': actions, 'date': current_date})

# Views para Agenda (acesso apenas para usuários logados)
@login_required
def agenda_home(request):
    # Mês e ano atual ou conforme parâmetros
    today = timezone.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Validar mês e ano
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
        
    # Obter primeiro e último dia do mês
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Eventos do mês (apenas aprovados)
    events = Event.objects.filter(
        approved=True,
        start_time__gte=first_day,
        start_time__lte=last_day + timedelta(days=1)
    ).order_by('start_time')
    
    # Estruturar o calendário - Corrigir geração do calendário
    # Usamos a classe Calendar para garantir semanas corretas
    cal_obj = calendar.Calendar(firstweekday=6)  # 6 = domingo como primeiro dia da semana
    cal = cal_obj.monthdayscalendar(year, month)
    
    # Horários de funcionamento
    lab_schedule = LabSchedule.objects.all().order_by('day_of_week')
    
    # Dados para navegação do calendário
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # Month name in Portuguese
    month_names = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    month_name = month_names[month]
    
    # Adicionar contagem de eventos pendentes para administradores
    pending_count = 0
    if request.user.is_staff:
        pending_count = Event.objects.filter(approved=False).count()
    
    context = {
        'events': events,
        'calendar': cal,
        'month': month,
        'month_name': month_name,
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'lab_schedule': lab_schedule,
        'pending_count': pending_count,
    }
    
    return render(request, 'logs/agenda_home.html', context)

@login_required
def agenda_event_detail(request, event_id):
    # Se for um administrador, pode ver qualquer evento
    if request.user.is_staff:
        event = get_object_or_404(Event, id=event_id)
    else:
        # Se não for admin, só pode ver eventos aprovados
        event = get_object_or_404(Event, id=event_id, approved=True)
    
    return render(request, 'logs/agenda_event_detail.html', {'event': event})

@user_passes_test(staff_check)  # Apenas administradores podem criar eventos
def agenda_create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            
            # Administradores podem criar eventos aprovados automaticamente
            if request.user.is_staff:
                event.approved = True
            
            event.save()
            
            messages.success(request, 'Evento criado com sucesso!')
            return redirect('logs:agenda_home')
    else:
        form = EventForm()
    
    return render(request, 'logs/agenda_create_event.html', {'form': form})

@login_required
def agenda_request_visit(request):
    if request.method == 'POST':
        form = VisitRequestForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            # Não precisamos definir novamente o event_type aqui, ele já vem no formulário
            # e está sendo definido como inicial no __init__ do formulário
            
            # O usuário logado é o criador do evento
            event.created_by = request.user
            
            event.save()
            
            # Adicionar detalhes da visita na descrição
            visitor_info = (
                f"Solicitante: {form.cleaned_data['visitor_name']}\n"
                f"Email: {form.cleaned_data['visitor_email']}\n"
                f"Telefone: {form.cleaned_data['visitor_phone']}\n"
                f"Número de visitantes: {form.cleaned_data['number_of_visitors']}\n\n"
                f"Descrição da visita:\n{event.description}"
            )
            event.description = visitor_info
            event.save()
            
            # Enviar email de confirmação de solicitação
            try:
                enviar_email_solicitacao_enviada(event)
            except Exception as e:
                # Registrar erro mas não impedir o fluxo
                print(f"Erro ao enviar email de solicitação: {e}")
            
            messages.success(request, 'Solicitação de visita enviada com sucesso! Aguardando aprovação.')
            return redirect('logs:agenda_home')
    else:
        # Preencher os dados básicos do usuário logado
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'visitor_name': f"{request.user.first_name} {request.user.last_name}",
                'visitor_email': request.user.email
            }
        form = VisitRequestForm(initial=initial_data)
    
    return render(request, 'logs/agenda_request_visit.html', {'form': form})

@user_passes_test(staff_check)
def agenda_approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.approved = True
    event.save()
    
    # Enviar email de aprovação
    try:
        enviar_email_solicitacao_aprovada(event)
    except Exception as e:
        # Registrar erro mas não impedir o fluxo
        print(f"Erro ao enviar email de aprovação: {e}")
    
    messages.success(request, f'O evento "{event.title}" foi aprovado com sucesso!')
    
    # Verificar de onde veio a requisição para redirecionar apropriadamente
    referer = request.META.get('HTTP_REFERER', '')
    if 'pendentes' in referer:
        return redirect('logs:pending_events')
    else:
        return redirect('logs:agenda_home')

@user_passes_test(staff_check)
def agenda_delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    title = event.title
    event.delete()
    messages.success(request, f'O evento "{title}" foi excluído com sucesso!')
    
    # Verificar de onde veio a requisição para redirecionar apropriadamente
    referer = request.META.get('HTTP_REFERER', '')
    if 'pendentes' in referer:
        return redirect('logs:pending_events')
    else:
        return redirect('logs:agenda_home')

@user_passes_test(staff_check)
def pending_events(request):
    """View para exibir todos os eventos pendentes de aprovação"""
    pending = Event.objects.filter(approved=False).order_by('start_time')
    
    # Separe os eventos por tipo para facilitar a visualização
    visit_requests = pending.filter(event_type=Event.EventType.VISIT)
    other_events = pending.exclude(event_type=Event.EventType.VISIT)
    
    context = {
        'visit_requests': visit_requests,
        'other_events': other_events
    }
    
    return render(request, 'logs/pending_events.html', context)