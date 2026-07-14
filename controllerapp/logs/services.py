"""
Agendamento inteligente de visitas: alocação automática de monitor com base
na disponibilidade declarada por cada um no perfil (users.MonitorDisponibilidade).

Regras:
- Só é candidato quem marcou TODOS os slots de hora cobertos pela visita.
- Preferência para monitores sem nenhuma visita no horário (carga 0).
- Um monitor só recebe uma 2ª visita simultânea se nenhum outro candidato
  estiver livre no horário. Ninguém acompanha mais de 2 visitas ao mesmo tempo.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

MAX_VISITAS_SIMULTANEAS = 2


def _dia_e_horas_cobertas(start_time, end_time):
    """Dia da semana e lista de horas cheias que a visita ocupa (horário local)."""
    inicio = timezone.localtime(start_time)
    fim = timezone.localtime(end_time)
    ultima_hora = fim.hour + (1 if (fim.minute or fim.second) else 0)
    if fim.date() != inicio.date():
        # Visita cruzando a meia-noite: fora do escopo da alocação automática
        return inicio.weekday(), None
    return inicio.weekday(), list(range(inicio.hour, max(ultima_hora, inicio.hour + 1)))


def _carga_no_horario(monitor, start_time, end_time, excluir_event_id=None):
    """Quantas visitas aprovadas do monitor se sobrepõem ao intervalo."""
    from .models import Event
    qs = Event.objects.filter(
        monitor_responsavel=monitor,
        approved=True,
        event_type=Event.EventType.VISIT,
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if excluir_event_id:
        qs = qs.exclude(pk=excluir_event_id)
    return qs.count()


def alocar_monitor_para_visita(start_time, end_time, excluir_event_id=None):
    """
    Retorna o monitor escolhido para a visita, ou None se ninguém puder atender
    (caso em que a solicitação fica pendente de aprovação manual).
    """
    from users.models import MonitorDisponibilidade
    from .models import Event

    User = get_user_model()
    dia, horas = _dia_e_horas_cobertas(start_time, end_time)
    if not horas:
        return None

    # Candidatos: ativos que marcaram todas as horas do intervalo nesse dia
    cobertura = (
        MonitorDisponibilidade.objects
        .filter(dia_semana=dia, hora__in=horas, user__is_active=True)
        .values('user')
        .annotate(n=Count('hora'))
        .filter(n__gte=len(horas))
    )
    candidatos = list(User.objects.filter(pk__in=[c['user'] for c in cobertura]))
    if not candidatos:
        return None

    por_carga = {0: [], 1: []}
    for monitor in candidatos:
        carga = _carga_no_horario(monitor, start_time, end_time, excluir_event_id)
        if carga < MAX_VISITAS_SIMULTANEAS:
            por_carga[carga].append(monitor)

    livres = por_carga[0]
    if livres:
        # Balanceamento: entre os livres, quem tem menos visitas futuras atribuídas
        return min(
            livres,
            key=lambda m: Event.objects.filter(
                monitor_responsavel=m,
                event_type=Event.EventType.VISIT,
                start_time__gte=timezone.now(),
            ).count(),
        )

    # Ninguém livre: permite a 2ª visita simultânea para quem tem apenas 1
    ocupados_com_folga = por_carga[1]
    if ocupados_com_folga:
        return ocupados_com_folga[0]

    return None
