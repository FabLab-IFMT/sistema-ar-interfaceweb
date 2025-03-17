from django.db import models
from django.core.mail import send_mail
from django.conf import settings

def enviar_email_boas_vindas(usuario):
    """
    Envia um email de boas-vindas para o novo usuário registrado.
    
    Args:
        usuario: O objeto usuário que acabou de se registrar
    """
    assunto = f'Bem-vindo(a) ao Sistema de Gestão do Laboratório, {usuario.first_name}!'
    mensagem = f"""
    Olá {usuario.first_name} {usuario.last_name},
    
    Seja bem-vindo(a) ao nosso Sistema de Gestão do Laboratório!
    
    Seu cadastro foi realizado com sucesso. Agora você pode acessar todas as funcionalidades disponíveis para o seu perfil.
    
    Seus dados de acesso são:
    - Matrícula: {usuario.id}
    - Email: {usuario.email}
    
    Acesse o sistema através do link: http://localhost:8000/
    
    Em caso de dúvidas, entre em contato conosco.
    
    Atenciosamente,
    Equipe do Sistema de Gestão do Laboratório
    """
    
    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]
    
    return send_mail(
        assunto,
        mensagem,
        email_de,
        email_para,
        fail_silently=False,
    )

def enviar_email_solicitacao_enviada(evento):
    """
    Envia um email confirmando que a solicitação de evento/visita foi recebida.
    
    Args:
        evento: O objeto Event que foi solicitado
    """
    usuario = evento.created_by
    assunto = f'Sua solicitação foi recebida - {evento.title}'
    mensagem = f"""
    Olá {usuario.first_name} {usuario.last_name},
    
    Sua solicitação para o evento "{evento.title}" foi recebida com sucesso!
    
    Detalhes da solicitação:
    - Tipo: {evento.get_event_type_display()}
    - Data de início: {evento.start_time.strftime('%d/%m/%Y %H:%M')}
    - Data de término: {evento.end_time.strftime('%d/%m/%Y %H:%M')}
    
    Nossa equipe irá analisar sua solicitação e você receberá uma confirmação quando ela for aprovada.
    
    Atenciosamente,
    Equipe do Sistema de Gestão do Laboratório
    """
    
    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]
    
    return send_mail(
        assunto,
        mensagem,
        email_de,
        email_para,
        fail_silently=False,
    )

def enviar_email_solicitacao_aprovada(evento):
    """
    Envia um email notificando que a solicitação de evento/visita foi aprovada.
    
    Args:
        evento: O objeto Event que foi aprovado
    """
    usuario = evento.created_by
    assunto = f'Solicitação aprovada - {evento.title}'
    mensagem = f"""
    Olá {usuario.first_name} {usuario.last_name},
    
    Temos boas notícias! Sua solicitação para o evento "{evento.title}" foi aprovada.
    
    Detalhes do evento:
    - Tipo: {evento.get_event_type_display()}
    - Data de início: {evento.start_time.strftime('%d/%m/%Y %H:%M')}
    - Data de término: {evento.end_time.strftime('%d/%m/%Y %H:%M')}
    
    Você pode visualizar todos os detalhes do evento em nosso sistema.
    
    Atenciosamente,
    Equipe do Sistema de Gestão do Laboratório
    """
    
    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]
    
    return send_mail(
        assunto,
        mensagem,
        email_de,
        email_para,
        fail_silently=False,
    )
