from django.db.models import Count
from django.utils import timezone
from .models import Action, Event

def pending_events_count(request):
    """
    Adiciona o número de eventos pendentes ao contexto para usuários administradores.
    """
    context = {'global_pending_count': 0}
    
    # Verificar se o usuário está autenticado e é staff
    if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
        # Contar eventos pendentes de aprovação
        context['global_pending_count'] = Event.objects.filter(approved=False).count()
    
    return context
