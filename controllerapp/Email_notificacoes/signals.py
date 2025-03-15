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
    if created:  # Se é um novo usuário (não uma atualização)
        enviar_email_boas_vindas(instance)
