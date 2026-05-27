import logging
import threading
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def enviar_email_async(assunto, mensagem, email_de, email_para, html_message=None):
    """
    Envia e-mail em background usando uma thread não-daemon.

    A thread não é daemon para que o processo aguarde o envio ao encerrar
    graciosamente (SIGTERM via gunicorn). Para maior confiabilidade em
    produção, considere migrar para Celery + Redis.

    Args:
        assunto: Assunto do e-mail
        mensagem: Corpo em texto simples (fallback para clientes sem HTML)
        email_de: Endereço do remetente
        email_para: Lista de destinatários
        html_message: Versão HTML do e-mail (opcional)
    """
    def _enviar():
        try:
            send_mail(
                assunto,
                mensagem,
                email_de,
                email_para,
                fail_silently=False,
                html_message=html_message,
            )
        except Exception:
            logger.exception(
                "Falha ao enviar e-mail | assunto=%r | para=%r",
                assunto,
                email_para,
            )

    thread = threading.Thread(target=_enviar, daemon=False)
    thread.start()
    return True
