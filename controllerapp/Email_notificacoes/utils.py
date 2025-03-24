import threading
from django.core.mail import send_mail

def enviar_email_async(assunto, mensagem, email_de, email_para, html_message=None):
    """
    Função para enviar email de forma assíncrona usando threads.
    
    Args:
        assunto: Assunto do email
        mensagem: Corpo do email em texto simples
        email_de: Email do remetente
        email_para: Lista de emails dos destinatários
        html_message: Versão HTML do email (opcional)
    """
    def envio_em_background():
        try:
            send_mail(
                assunto,
                mensagem,
                email_de,
                email_para,
                fail_silently=False,
                html_message=html_message
            )
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
    
    # Criando e iniciando a thread
    thread_email = threading.Thread(target=envio_em_background)
    thread_email.daemon = True  # A thread será encerrada quando o programa principal terminar
    thread_email.start()
    
    return True
