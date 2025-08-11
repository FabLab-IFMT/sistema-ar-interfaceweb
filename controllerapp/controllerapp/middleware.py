from django.conf import settings
from django.shortcuts import redirect

class MaintenanceModeMiddleware:
    """
    Intercepta todas as requisições quando MAINTENANCE_MODE=True
    e redireciona para a página de manutenção, exceto:
    - a própria rota de manutenção
    - arquivos estáticos (STATIC_URL)
    - arquivos de mídia (MEDIA_URL)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            path = request.path or '/'
            static_url = getattr(settings, 'STATIC_URL', '/static/')
            media_url = getattr(settings, 'MEDIA_URL', '/media/')

            is_allowed = (
                path.startswith('/maintenance') or
                (static_url and path.startswith(static_url)) or
                (media_url and path.startswith(media_url))
            )

            if not is_allowed:
                return redirect('/maintenance/')

        return self.get_response(request)
