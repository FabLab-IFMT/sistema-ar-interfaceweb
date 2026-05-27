from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser
from .models import enviar_email_boas_vindas

@receiver(post_save, sender=CustomUser)
def enviar_email_apos_registro(sender, instance, created, **kwargs):
    """
    Sinal que é acionado após um usuário ser salvo.
    Envia um email de boas-vindas para novos usuários.
    """
    # Só envia boas-vindas quando o usuário já está ativo (ex: criado pelo admin).
    # No fluxo de auto-cadastro, is_active=False até a confirmação do email;
    # o email de boas-vindas é enviado em confirm_email após a ativação.
    if created and instance.is_active:
        enviar_email_boas_vindas(instance)
