
from .models import ProjectistRequest

def registration_requests_count(request):
    """Context processor para adicionar contador de solicitações pendentes ao contexto global"""
    pending_count = 0
    if hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
        if user.is_superuser or user.is_staff or user.has_role('gestor_projetos'):
            pending_count = ProjectistRequest.objects.filter(status='pending').count()
    
    return {
        'registration_pending_count': pending_count
    }