from django.db.models import Count
from django.utils import timezone
from .models import Action, Event

def pending_events_count(request):
    """Fornece contagem de eventos pendentes para o layout geral"""
    context = {}
    
    # Só adicionar para usuários staff
    if request.user.is_authenticated and request.user.is_staff:
        context['pending_events_count'] = Event.objects.filter(approved=False).count()
        
        # Adicionar contagem de erros recentes (últimos 7 dias)
        one_week_ago = timezone.now().date() - timezone.timedelta(days=7)
        context['recent_errors_count'] = Action.objects.filter(
            date__gte=one_week_ago,
            severity__in=['error', 'critical']
        ).count()
    
    return context
