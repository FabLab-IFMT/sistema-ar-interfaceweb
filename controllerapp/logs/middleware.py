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
        # Processar a requisição normalmente, sem registrar ações regulares
        try:
            response = self.get_response(request)
            
            # Registrar apenas erros do servidor (500, etc.)
            if response.status_code >= 500:
                self._log_server_error(request, response)
                
            return response
            
        except PermissionDenied:
            # Registrar acessos negados (403)
            self._log_access_denied(request)
            raise
        
        except Exception as e:
            # Registrar exceções não tratadas
            self._log_exception(request, e)
            raise
    
    def _log_access_denied(self, request):
        """Registra tentativas de acesso não autorizado"""
        try:
            now = timezone.now()
            username = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anônimo'
            
            Action.objects.create(
                author=username,
                type='Acesso Negado',
                description=f"Tentativa de acesso à área restrita: {request.path}",
                date=now.date(),
                time=now.time(),
                url=request.path,
                severity='security',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Se falhar ao registrar o erro, simplesmente prosseguir
            print(f"Erro ao registrar log: {e}")
    
    def _log_server_error(self, request, response):
        """Registra erros de servidor"""
        try:
            now = timezone.now()
            username = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anônimo'
            
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
        except Exception as e:
            # Se falhar ao registrar o erro, simplesmente prosseguir
            print(f"Erro ao registrar log: {e}")
    
    def _log_exception(self, request, exception):
        """Registra exceções não tratadas"""
        try:
            now = timezone.now()
            username = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anônimo'
            
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
        except Exception as e:
            # Se falhar ao registrar o erro, simplesmente prosseguir
            print(f"Erro ao registrar log: {e}")
    
    def _get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# Removemos todos os receivers de signals para evitar problemas
