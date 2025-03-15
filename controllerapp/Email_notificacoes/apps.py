from django.apps import AppConfig


class EmailNotificacoesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Email_notificacoes'
    
    def ready(self):
        import Email_notificacoes.signals  # Importa os sinais quando o app for carregado
