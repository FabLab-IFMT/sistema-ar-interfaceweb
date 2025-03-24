import datetime
import json
from django.urls import resolve
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import Action
from .utils import log_user_action

class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Registrar o início da requisição para requests importantes
        if self._should_log_request(request):
            self._log_request_start(request)
        
        # Processar a requisição
        try:
            response = self.get_response(request)
            
            # Registrar tentativas de acesso não autorizado (403)
            if response.status_code == 403:
                self._log_access_denied(request)
                
            # Registrar erros 404
            elif response.status_code == 404:
                self._log_not_found(request)
                
            # Registrar erros de servidor (500, etc.)
            elif response.status_code >= 500:
                self._log_server_error(request, response)
                
            # Registrar ações administrativas bem-sucedidas
            elif self._is_admin_post_action(request, response):
                self._log_admin_action(request, response)
                
            return response
            
        except PermissionDenied:
            # Capturar exceções de permissão negada
            self._log_access_denied(request)
            raise
        
        except Exception as e:
            # Capturar exceções genéricas
            self._log_exception(request, e)
            raise
    
    def _should_log_request(self, request):
        """Determina se uma requisição deve ser registrada"""
        # Não logar requisições de arquivos estáticos ou media
        if any(path in request.path for path in ['/static/', '/media/']):
            return False
            
        # Ignorar explicitamente requisições de logout para evitar o erro
        if '/users/logout/' in request.path:
            return False
            
        # Sempre registrar POST, PUT, DELETE
        if request.method in ('POST', 'PUT', 'DELETE'):
            return True
            
        # Registrar acessos ao admin
        if '/admin/' in request.path and request.user.is_authenticated:
            return True
            
        # Outras regras podem ser adicionadas
        
        return False
    
    def _log_request_start(self, request):
        """Registra o início de uma requisição importante"""
        if not request.user.is_authenticated:
            return
            
        now = timezone.now()
        
        # Criar descrição baseada no tipo de requisição
        if request.method == 'POST':
            action_type = 'Envio de Formulário'
            description = f"Usuário enviou dados via POST para: {request.path}"
        elif request.method in ('PUT', 'DELETE'):
            action_type = 'Modificação de Dados'
            description = f"Usuário realizou {request.method} em: {request.path}"
        elif '/admin/' in request.path:
            action_type = 'Acesso Administrativo'
            description = f"Usuário acessou área administrativa: {request.path}"
        else:
            action_type = 'Acesso ao Sistema'
            description = f"Usuário acessou: {request.path}"
        
        Action.objects.create(
            author=request.user.username,
            type=action_type,
            description=description,
            date=now.date(),
            time=now.time(),
            url=request.path,
            severity='info',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _log_access_denied(self, request):
        """Registra tentativas de acesso não autorizado"""
        now = timezone.now()
        username = request.user.username if request.user.is_authenticated else 'Anônimo'
        
        Action.objects.create(
            author=username,
            type='Tentativa de Acesso Não Autorizado',
            description=f"Tentativa de acesso à área restrita: {request.path}",
            date=now.date(),
            time=now.time(),
            url=request.path,
            severity='security',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _log_not_found(self, request):
        """Registra erros 404"""
        now = timezone.now()
        username = request.user.username if request.user.is_authenticated else 'Anônimo'
        
        Action.objects.create(
            author=username,
            type='Página Não Encontrada',
            description=f"URL não encontrada: {request.path}",
            date=now.date(),
            time=now.time(),
            url=request.path,
            severity='warning',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _log_server_error(self, request, response):
        """Registra erros de servidor"""
        now = timezone.now()
        username = request.user.username if request.user.is_authenticated else 'Anônimo'
        
        Action.objects.create(
            author=username,
            type=f'Erro do Servidor (HTTP {response.status_code})',
            description=f"Erro de servidor ao acessar: {request.path}",
            date=now.date(),
            time=now.time(),
            url=request.path,
            severity='critical',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _is_admin_post_action(self, request, response):
        """Verifica se é uma ação POST no admin que foi bem-sucedida"""
        return (
            request.user.is_authenticated and 
            request.user.is_staff and 
            '/admin/' in request.path and 
            request.method == 'POST' and 
            response.status_code in (200, 201, 302)  # Sucesso ou redirecionamento
        )
    
    def _log_admin_action(self, request, response):
        """Registra ações administrativas"""
        now = timezone.now()
        
        # Tentar identificar o tipo de ação
        if 'delete' in request.path:
            action_type = 'Exclusão Administrativa'
        elif 'add' in request.path:
            action_type = 'Criação Administrativa'
        else:
            action_type = 'Modificação Administrativa'
        
        # Identificar o modelo sendo alterado
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[0] == 'admin':
            model_name = path_parts[2]
        else:
            model_name = 'desconhecido'
        
        Action.objects.create(
            author=request.user.username,
            type=action_type,
            description=f"{action_type} no modelo {model_name}",
            date=now.date(),
            time=now.time(),
            url=request.path,
            severity='info',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _log_exception(self, request, exception):
        """Registra exceções não tratadas"""
        now = timezone.now()
        username = request.user.username if request.user.is_authenticated else 'Anônimo'
        
        Action.objects.create(
            author=username,
            type='Erro do Sistema',
            description=f"Exceção: {type(exception).__name__} - {str(exception)}",
            date=now.date(),
            time=now.time(),
            url=request.path,
            severity='error',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Conectar aos sinais de login e logout
@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """Registra eventos de login"""
    now = timezone.now()
    
    log_user_action(
        user=user,
        action_type='Login',
        description=f"Usuário {user.username} entrou no sistema",
        severity='info',
        request=request
    )

# Modificar o receiver do logout para evitar duplicidade
@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """Registra eventos de logout"""
    # Não faz nada aqui, pois agora estamos registrando o logout na view
    # A view logout_view já está tratando do log manualmente
    pass
