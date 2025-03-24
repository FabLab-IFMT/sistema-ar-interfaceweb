from .models import Action


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
    author = kwargs.get("author")
    param1 = kwargs.get("param1")
    param2 = kwargs.get ("param2")

    if not author: author = "Desconhecido"
    if not param1: param1 = "Parâmetro 1 não especificado"
    if not param2: param2 = "Parâmetro 2 não especificado"

    Action.objects.create(author=author, type=type, param1=param1, param2=param2 )


