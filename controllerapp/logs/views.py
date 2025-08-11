from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count
from datetime import datetime, timedelta, date
import calendar
from .models import Action, Event, LabSchedule
from .scripts import FormattedAction
from .forms import EventForm, VisitRequestForm, EventRejectForm
from .utils import log_user_action
from Email_notificacoes.models import enviar_email_solicitacao_enviada, enviar_email_solicitacao_aprovada, enviar_email_solicitacao_recusada
# Importe a função do seu arquivo google_calendar.py
from .google_calendar import get_google_calendar_events

def staff_check(user):
    return user.is_staff

# Views para logs (acesso apenas para staff)
@user_passes_test(staff_check)
def logs_list(request):
    # Obter datas distintas com ações, ordenadas por data decrescente
    # Também contamos o número de ações por data e o nível mais alto de severidade
    dates_with_stats = Action.objects.values('date')\
        .annotate(count=Count('id'))\
        .order_by('-date')
    
    # Para cada data, verificamos o nível máximo de severidade
    for date_stat in dates_with_stats:
        # Verificar se há erros críticos
        if Action.objects.filter(date=date_stat['date'], severity='critical').exists():
            date_stat['max_severity'] = 'critical'
        # Verificar se há erros
        elif Action.objects.filter(date=date_stat['date'], severity='error').exists():
            date_stat['max_severity'] = 'error'
        # Verificar se há alertas de segurança
        elif Action.objects.filter(date=date_stat['date'], severity='security').exists():
            date_stat['max_severity'] = 'security'
        # Verificar se há avisos
        elif Action.objects.filter(date=date_stat['date'], severity='warning').exists():
            date_stat['max_severity'] = 'warning'
        # Se não, é informativo
        else:
            date_stat['max_severity'] = 'info'
    
    return render(request, 'logs/logs_list.html', {'dates_with_stats': dates_with_stats})

@user_passes_test(staff_check)
def logs_datepage(request, day, month, year):
    # Filtrar por severidade se fornecido
    severity = request.GET.get('severity')
    
    actions_query = Action.objects.filter(date=date(year, month, day))
    
    if (severity):
        actions_query = actions_query.filter(severity=severity)
    
    # Ordenar por hora e formatar
    actions = [FormattedAction(action) for action in actions_query.order_by('time')]
    current_date = date(year, month, day)
    
    # Estatísticas para este dia
    stats = {
        'total': actions_query.count(),
        'errors': actions_query.filter(severity__in=['error', 'critical']).count(),
        'warnings': actions_query.filter(severity='warning').count(),
        'security': actions_query.filter(severity='security').count(),
    }
    
    return render(request, 'logs/logs_datepage.html', {
        'actions': actions, 
        'date': current_date,
        'stats': stats,
        'active_severity': severity,
    })

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
    last_day = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
    
    # 1. Buscar eventos locais (aprovados) do banco de dados
    local_events = Event.objects.filter(
        approved=True,
        start_time__gte=first_day,
        start_time__lte=last_day + timedelta(days=1)
    ).order_by('start_time')
    
    # 2. Buscar eventos do Google Calendar
    # Somente superusuários podem ver itens do Google
    google_events_raw = get_google_calendar_events(first_day, last_day) if request.user.is_superuser else []

    # 3. Processar e combinar todos os eventos
    all_events = []
    
    # Adicionar eventos locais à lista combinada
    for event in local_events:
        all_events.append({
            'id': event.id,
            'title': event.title,
            'start_time': event.start_time,
            'end_time': event.end_time,
            'event_type': event.event_type,
            'get_event_type_display': event.get_event_type_display,
            'description': event.description,
            'is_google': False # Flag para identificar no template
        })

    # Adicionar eventos do Google à lista combinada
    for event in google_events_raw:
        start_str = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
        end_str = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
        
        if start_str:
            # Lida com eventos de dia inteiro (formato 'YYYY-MM-DD')
            if 'T' not in start_str:
                start_time = timezone.make_aware(datetime.strptime(start_str, '%Y-%m-%d'))
                end_time = timezone.make_aware(datetime.strptime(end_str, '%Y-%m-%d')) if end_str else start_time
            else:
                start_time = timezone.make_aware(datetime.fromisoformat(start_str.replace('Z', '+00:00')))
                end_time = timezone.make_aware(datetime.fromisoformat(end_str.replace('Z', '+00:00'))) if end_str else start_time

            all_events.append({
                'id': event.get('id'),
                'title': event.get('summary', 'Evento do Google'),
                'start_time': start_time,
                'end_time': end_time,
                'event_type': 'google', # Tipo customizado
                'get_event_type_display': 'Google Calendar',
                'description': event.get('description', ''),
                'is_google': True # Flag para identificar no template
            })

    # Ordenar a lista combinada por data de início
    all_events.sort(key=lambda x: x['start_time'])
    
    # Estruturar o calendário
    cal_obj = calendar.Calendar(firstweekday=6)
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
        'events': all_events, # Passa a lista combinada para o template
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
            # Criar o evento com os dados separados de data e hora
            event = form.save(commit=False)
            
            # Usar os valores datetime criados na validação
            event.start_time = form.start_datetime
            event.end_time = form.end_datetime
            
            # Definir explicitamente o tipo de evento como visita
            event.event_type = Event.EventType.VISIT
            
            # O usuário logado é o criador do evento
            if request.user.is_authenticated:
                event.created_by = request.user
            
            event.save()
            
            # Adicionar detalhes da visita na descrição
            visitor_info = (
                f"Solicitante: {form.cleaned_data['visitor_name']}\n"
                f"Email: {form.cleaned_data['visitor_email']}\n"
                f"Telefone: {form.cleaned_data['visitor_phone']}\n"
                f"Número de visitantes: {form.cleaned_data['number_of_visitors']}\n"
                f"Data da visita: {form.cleaned_data['visit_date'].strftime('%d/%m/%Y')}\n"
                f"Horário: {form.cleaned_data['start_hour'].strftime('%H:%M')} - {form.cleaned_data['end_hour'].strftime('%H:%M')}\n\n"
                f"Detalhes adicionais:\n{event.description}"
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
    
    # Se o evento não está aprovado, consideramos como uma rejeição de solicitação
    # e redirecionamos para a tela de rejeição para coletar o motivo
    if not event.approved:
        return redirect('logs:agenda_reject_event', event_id=event_id)
    
    # Se o evento já estava aprovado, apenas excluímos sem pedir motivo
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
def agenda_reject_event(request, event_id):
    """View para rejeitar uma solicitação de evento/visita e enviar email de notificação."""
    event = get_object_or_404(Event, id=event_id)
    
    # Verificar se o evento já está aprovado
    if event.approved:
        messages.error(request, "Não é possível rejeitar um evento já aprovado.")
        return redirect('logs:agenda_home')
    
    referer_url = request.META.get('HTTP_REFERER', '')
    
    if request.method == 'POST':
        form = EventRejectForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo']
            
            # Enviar email de recusa antes de excluir o evento
            try:
                enviar_email_solicitacao_recusada(event, motivo)
            except Exception as e:
                # Registrar erro mas não impedir o fluxo
                print(f"Erro ao enviar email de recusa: {e}")
            
            # Registrar a ação
            action_type = 'Recusa de Solicitação'
            action_desc = f"Rejeitou a solicitação '{event.title}' do usuário {event.created_by.first_name} {event.created_by.last_name}"
            log_user_action(
                user=request.user,
                action_type=action_type,
                description=action_desc,
                severity='info',
                request=request
            )
            
            # Excluir o evento
            title = event.title
            event.delete()
            
            messages.success(request, f'A solicitação "{title}" foi recusada e o solicitante foi notificado.')
            
            # Verificar de onde veio a requisição para redirecionar
            if 'pendentes' in referer_url:
                return redirect('logs:pending_events')
            else:
                return redirect('logs:agenda_home')
    else:
        form = EventRejectForm()
    
    return render(request, 'logs/agenda_reject_event.html', {
        'form': form,
        'event': event,
        'referer_url': referer_url
    })

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