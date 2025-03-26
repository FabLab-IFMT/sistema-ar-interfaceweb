
from .models import RegistrationRequest

def registration_requests_count(request):
    """Context processor para adicionar contador de solicitações pendentes ao contexto global"""
    pending_count = 0
    if request.user.is_authenticated and request.user.is_superuser:
        pending_count = RegistrationRequest.objects.filter(status='pending').count()
    
    return {
        'registration_pending_count': pending_count
    }