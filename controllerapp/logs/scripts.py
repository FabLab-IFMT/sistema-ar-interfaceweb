import traceback
from datetime import datetime
from .models import Action

class FormattedAction:
    def __init__(self, action):
        self.action = action
        self.id = action.id
        self.author = action.author
        self.type = action.type
        self.description = action.description
        self.date = action.date
        self.time = action.time
        self.user = action.user
        self.url = action.url
        self.ip_address = action.ip_address
        
        # Formata o tipo para exibição com classes CSS
        self.type_class = self.get_type_class()
        self.type_icon = self.get_type_icon()
        
    def get_type_class(self):
        type_classes = {
            'info': 'primary',
            'success': 'success',
            'warning': 'warning',
            'error': 'danger',
            'critical': 'dark'
        }
        return type_classes.get(self.action.type, 'secondary')
    
    def get_type_icon(self):
        type_icons = {
            'info': 'info-circle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle',
            'critical': 'bug'
        }
        return type_icons.get(self.action.type, 'question-circle')

def log_action(request=None, type='info', description='', user=None):
    """
    Registra uma ação no sistema
    """
    try:
        action = Action()
        action.type = type
        action.description = description
        
        # Se usuário for fornecido diretamente
        if user:
            action.user = user
            action.author = f"{user.first_name} {user.last_name}" if user.first_name else user.username
        # Se não, tenta obter do request
        elif request and request.user.is_authenticated:
            action.user = request.user
            action.author = f"{request.user.first_name} {request.user.last_name}" if request.user.first_name else request.user.username
        else:
            action.author = "Sistema"
        
        # Capturar informações adicionais do request
        if request:
            action.url = request.path
            action.ip_address = request.META.get('REMOTE_ADDR', '')
            action.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        action.save()
        return action
    except Exception as e:
        print(f"Erro ao registrar log: {str(e)}")
        return None

def log_error(request=None, error=None, description=None):
    """
    Registra um erro no sistema com stack trace
    """
    try:
        error_desc = description or str(error) or "Erro desconhecido"
        tb = traceback.format_exc() if error else ""
        
        action = Action()
        action.type = 'error'
        action.description = error_desc
        action.error_traceback = tb
        
        if request and request.user.is_authenticated:
            action.user = request.user
            action.author = f"{request.user.first_name} {request.user.last_name}" if request.user.first_name else request.user.username
        else:
            action.author = "Sistema"
        
        # Capturar informações adicionais do request
        if request:
            action.url = request.path
            action.ip_address = request.META.get('REMOTE_ADDR', '')
            action.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        action.save()
        return action
    except Exception as e:
        print(f"Erro ao registrar log de erro: {str(e)}")
        return None

# Função de compatibilidade para código existente
def create_log(author, type, description, date=None, time=None):
    """
    Função de compatibilidade para manter código existente funcionando.
    Recomenda-se usar log_action para novos desenvolvimentos.
    """
    try:
        action = Action()
        action.author = author
        action.type = type
        action.description = description
        
        # Se date e time não forem fornecidos, serão preenchidos automaticamente
        # com auto_now_add=True no modelo
        if date:
            action.date = date
        if time:
            action.time = time
            
        action.save()
        return action
    except Exception as e:
        print(f"Erro ao registrar log: {str(e)}")
        return None


