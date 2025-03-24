from .models import Action
from django.utils import timezone


class FormattedAction:
    def __init__(self, action):
        self.id = action.id
        self.author = action.author
        self.type = action.type
        self.description = action.description
        self.date = action.date
        self.time = action.time.strftime('%H:%M:%S')
        self.url = action.url
        self.severity = action.severity
        self.ip_address = action.ip_address
        self.user_agent = action.user_agent
        
        # Para facilitar no template
        self.is_error = action.severity in ['error', 'critical']
        self.is_warning = action.severity == 'warning'
        self.is_security = action.severity == 'security'
        
    def get_severity_class(self):
        """Retorna a classe CSS para esta severidade"""
        severity_classes = {
            'info': 'primary',
            'warning': 'warning',
            'error': 'danger',
            'critical': 'danger',
            'security': 'dark',
        }
        return severity_classes.get(self.severity, 'primary')


def create_log(type, **kwargs):
    # Modificando para permitir autor nulo
    author = kwargs.get("author", "Sistema")
    param1 = kwargs.get("param1", "Parâmetro 1 não especificado")
    param2 = kwargs.get ("param2", "Parâmetro 2 não especificado")

    # Criar o log sem validar que o autor não seja nulo
    Action.objects.create(
        author=author if author else None,  # Usar None se author for vazio
        type=type, 
        description=f"{param1} - {param2}",  # Adicionando uma descrição padrão
        date=timezone.now().date(),
        time=timezone.now().time()
    )


