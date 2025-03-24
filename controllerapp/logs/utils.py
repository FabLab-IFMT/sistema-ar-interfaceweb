from django.utils import timezone
from .models import Action

def log_user_action(user, action_type, description, severity='info', url=None, request=None):
    """
    Registra uma ação de usuário no sistema
    
    Args:
        user: O usuário que realizou a ação (ou string com identificação)
        action_type: Tipo da ação (login, logout, etc)
        description: Descrição detalhada da ação
        severity: Nível de severidade (info, warning, error, critical, security)
        url: URL relacionada à ação
        request: Objeto request para extrair informações adicionais
    """
    now = timezone.now()
    
    # Se temos um usuário autenticado, usar o username. Caso contrário, usar o parâmetro diretamente
    if hasattr(user, 'username'):
        username = user.username
    else:
        username = str(user)
    
    # Garantir que username nunca seja nulo ou vazio
    if not username:
        username = "Sistema"
    
    # Extrair informações adicionais do request, se disponível
    ip_address = None
    user_agent = None
    if request:
        # Obter IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Obter User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Obter URL do request se não fornecida explicitamente
        if not url:
            url = request.path
    
    # Criar registro
    Action.objects.create(
        author=username,
        type=action_type,
        description=description,
        date=now.date(),
        time=now.time(),
        url=url,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent
    )
