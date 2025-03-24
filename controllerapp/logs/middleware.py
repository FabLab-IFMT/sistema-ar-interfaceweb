import sys
import traceback
from django.utils.deprecation import MiddlewareMixin
from .scripts import log_error

class LogErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        """
        Captura exceções não tratadas e registra no log
        """
        log_error(request=request, error=exception)
        # Retornar None para permitir que o Django continue processando a exceção
        return None
