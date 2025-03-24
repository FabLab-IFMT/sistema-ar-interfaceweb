from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from datetime import datetime, timedelta, date
import calendar
from .models import Action, Event, LabSchedule
from .scripts import FormattedAction, log_action, log_error
from .forms import EventForm, VisitRequestForm
from Email_notificacoes.models import enviar_email_solicitacao_enviada, enviar_email_solicitacao_aprovada

def staff_check(user):
    return user.is_staff

# Views para logs (acesso apenas para staff)
@user_passes_test(staff_check)
def logs_list(request):
    # Log da ação de visualizar logs
    log_action(request, 'info', 'Acessou a lista de logs')
    
    # Filtros
    log_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    user_id = request.GET.get('user_id', '')
    
    # Query base
    actions = Action.objects.all().order_by('-date', '-time')
    
    # Aplicar filtros
    if log_type:
        actions = actions.filter(type=log_type)
    
    if search:
        actions = actions.filter(
            Q(author__icontains=search) | 
            Q(description__icontains=search) |
            Q(url__icontains=search)
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            actions = actions.filter(date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            actions = actions.filter(date__lte=date_to_obj)
        except ValueError:
            pass
            
    if user_id:
        actions = actions.filter(user_id=user_id)
    
    # Paginação
    paginator = Paginator(actions, 25)  # 25 logs por página
    page = request.GET.get('page')
    
    try:
        actions_page = paginator.page(page)
    except PageNotAnInteger:
        actions_page = paginator.page(1)
    except EmptyPage:
        actions_page = paginator.page(paginator.num_pages)
    
    # Formatar ações
    formatted_actions = [FormattedAction(action) for action in actions_page]
    
    # Estatísticas
    total_logs = actions.count()
    error_logs = actions.filter(type__in=['error', 'critical']).count()
    
    # Usuários únicos para filtro
    unique_users = Action.objects.exclude(user=None).values_list('user__id', 'user__username', 'user__first_name', 'user__last_name').distinct()
    
    # Preparar datas únicas para filtros
    dates = list(Action.objects.order_by('-date').values_list('date', flat=True).distinct())[:30]  # últimos 30 dias
    
    context = {
        'actions': formatted_actions,
        'page_obj': actions_page,
        'total_logs': total_logs,
        'error_logs': error_logs,
        'dates': dates,
        'log_type': log_type,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'user_id': user_id,
        'unique_users': unique_users,
    }

    return render(request, 'logs/logs_list.html', context)

@user_passes_test(staff_check)
def logs_datepage(request, day, month, year):
    # Registrar ação de visualização
    current_date = date(year, month, day)
    log_action(request, 'info', f'Visualizou logs do dia {current_date.strftime("%d/%m/%Y")}')
    
    # Filtrar ações pela data específica
    actions = Action.objects.filter(date=current_date).order_by('time')
    
    # Aplicar filtros adicionais
    log_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    user_id = request.GET.get('user_id', '')
    
    if log_type:
        actions = actions.filter(type=log_type)
    
    if search:
        actions = actions.filter(
            Q(author__icontains=search) | 
            Q(description__icontains=search) |
            Q(url__icontains=search)
        )
        
    if user_id:
        actions = actions.filter(user_id=user_id)
    
    # Formatar as ações
    formatted_actions = [FormattedAction(action) for action in actions]
    
    # Usuários únicos para filtro
    unique_users = Action.objects.filter(date=current_date).exclude(user=None).values_list(
        'user__id', 'user__username', 'user__first_name', 'user__last_name'
    ).distinct()
    
    context = {
        'actions': formatted_actions,
        'date': current_date,
        'log_type': log_type,
        'search': search,
        'user_id': user_id,
        'unique_users': unique_users
    }

    return render(request, 'logs/logs_datepage.html', context)

# Views para Agenda (acesso apenas para usuários logados)
@login_required
def agenda_home(request):
    # Log da ação
    log_action(request, 'info', 'Acessou a agenda')
    
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
    
    # Transformar o calendário em estrutura de dados mais útil para o template
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # Dia fora do mês atual
                week_data.append({
                    'day': None,
                    'events': [],
                    'is_today': False,
                    'is_past': False
                })
            else:
                # Verificar se o dia é hoje
                current_date = date(year, month, day)
                is_today = current_date == today.date()
                is_past = current_date < today.date()
                
                # Obter eventos para este dia
                day_events = [e for e in events if e.start_time.date() == current_date]
                
                week_data.append({
                    'day': day,
                    'events': day_events,
                    'is_today': is_today,
                    'is_past': is_past,
                    'date': current_date
                })
        calendar_data.append(week_data)
    
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
        'calendar_data': calendar_data,
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
    
    return render(request, 'agenda/agenda_home.html', context)

@login_required
def agenda_event_detail(request, event_id):
    # Se for um administrador, pode ver qualquer evento
    if request.user.is_staff:
        event = get_object_or_404(Event, id=event_id)
    else:
        # Se não for admin, só pode ver eventos aprovados
        event = get_object_or_404(Event, id=event_id, approved=True)
    
    # Log da ação
    log_action(request, 'info', f'Visualizou detalhes do evento: {event.title}')
    
    return render(request, 'agenda/agenda_event_detail.html', {'event': event})

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
            
            # Log da ação
            log_action(request, 'success', f'Criou um novo evento: {event.title}')
            
            messages.success(request, 'Evento criado com sucesso!')
            return redirect('logs:agenda_home')
    else:
        form = EventForm()
    
    return render(request, 'agenda/agenda_create_event.html', {'form': form})

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
            
            # O usuário logado é o criador do evento
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
            
            # Log da ação
            log_action(request, 'success', f'Solicitou uma visita para o dia {form.cleaned_data["visit_date"].strftime("%d/%m/%Y")}')
            
            # Enviar email de confirmação de solicitação
            try:
                enviar_email_solicitacao_enviada(event)
            except Exception as e:
                # Registrar erro no log
                log_error(request, e, f"Erro ao enviar email de solicitação para evento {event.id}")
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
    
    return render(request, 'agenda/agenda_request_visit.html', {'form': form})

@user_passes_test(staff_check)
def agenda_approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.approved = True
    event.save()
    
    # Log da ação
    log_action(request, 'success', f'Aprovou o evento: {event.title}')
    
    # Enviar email de aprovação
    try:
        enviar_email_solicitacao_aprovada(event)
    except Exception as e:
        # Registrar erro no log
        log_error(request, e, f"Erro ao enviar email de aprovação para evento {event.id}")
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
    
    # Log da ação antes de excluir
    log_action(request, 'warning', f'Excluiu o evento: {title}')
    
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
    # Log da ação
    log_action(request, 'info', 'Acessou a lista de eventos pendentes')
    
    pending = Event.objects.filter(approved=False).order_by('start_time')
    
    # Separe os eventos por tipo para facilitar a visualização
    visit_requests = pending.filter(event_type=Event.EventType.VISIT)
    other_events = pending.exclude(event_type=Event.EventType.VISIT)
    
    context = {
        'visit_requests': visit_requests,
        'other_events': other_events
    }
    
    return render(request, 'agenda/pending_events.html', context)

@login_required
def user_calendar(request):
    """View para exibir o calendário com apenas os eventos do usuário atual"""
    # Log da ação
    log_action(request, 'info', 'Acessou seu calendário pessoal')
    
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
    
    # Eventos do usuário
    user_events = Event.objects.filter(
        Q(created_by=request.user) | Q(participants=request.user),
        start_time__gte=first_day,
        start_time__lte=last_day + timedelta(days=1)
    ).distinct().order_by('start_time')
    
    # Estruturar o calendário igual ao agenda_home
    cal_obj = calendar.Calendar(firstweekday=6)
    cal = cal_obj.monthdayscalendar(year, month)
    
    # Transformar o calendário em estrutura de dados mais útil para o template
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # Dia fora do mês atual
                week_data.append({
                    'day': None,
                    'events': [],
                    'is_today': False,
                    'is_past': False
                })
            else:
                # Verificar se o dia é hoje
                current_date = date(year, month, day)
                is_today = current_date == today.date()
                is_past = current_date < today.date()
                
                # Obter eventos para este dia
                day_events = [e for e in user_events if e.start_time.date() == current_date]
                
                week_data.append({
                    'day': day,
                    'events': day_events,
                    'is_today': is_today,
                    'is_past': is_past,
                    'date': current_date
                })
        calendar_data.append(week_data)
    
    # Month name in Portuguese
    month_names = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    month_name = month_names[month]
    
    # Dados para navegação do calendário
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'events': user_events,
        'calendar_data': calendar_data,
        'month': month,
        'month_name': month_name,
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'is_user_calendar': True
    }
    
    return render(request, 'agenda/user_calendar.html', context)