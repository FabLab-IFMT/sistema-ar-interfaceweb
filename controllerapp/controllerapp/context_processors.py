from django.conf import settings


def umami(request):
    """
    Injeta as configurações do Umami (analytics auto-hospedado) em todos
    os templates. O snippet só é renderizado quando UMAMI_SCRIPT_URL estiver
    preenchido — em desenvolvimento permanece desativado.
    """
    return {
        'UMAMI_SCRIPT_URL': getattr(settings, 'UMAMI_SCRIPT_URL', ''),
        'UMAMI_WEBSITE_ID': getattr(settings, 'UMAMI_WEBSITE_ID', ''),
    }
