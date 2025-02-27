from .models import Event

def pending_events_count(request):
    """
    Adiciona a contagem de eventos pendentes ao contexto global para administradores
    """
    context = {
        'global_pending_count': 0
    }
    
    # Verificar se o usuário está autenticado e é staff
    if request.user.is_authenticated and request.user.is_staff:
        context['global_pending_count'] = Event.objects.filter(approved=False).count()
    
    return context
