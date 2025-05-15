from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
# Importar nova função de envio assíncrono
from .utils import enviar_email_async

def enviar_email_boas_vindas(usuario):
    """
    Envia um email de boas-vindas para o novo usuário registrado.
    
    Args:
        usuario: O objeto usuário que acabou de se registrar
    """
    assunto = f'Bem-vindo(a) ao Sistema de Gestão do Laboratório, {usuario.first_name}!'
    
    # Criar conteúdo do email em HTML
    contexto = {'usuario': usuario}
    html_mensagem = render_to_string('emails/boas_vindas.html', contexto)
    
    # Texto simples para clientes de email que não suportam HTML
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
    
    return enviar_email_async(
        assunto,
        mensagem,
        email_de,
        email_para,
        html_message=html_mensagem
    )

def enviar_email_solicitacao_enviada(evento):
    """
    Envia um email confirmando que a solicitação de evento/visita foi recebida.
    
    Args:
        evento: O objeto Event que foi solicitado
    """
    usuario = evento.created_by
    assunto = f'Sua solicitação foi recebida - {evento.title}'
    
    # Criar conteúdo do email em HTML
    contexto = {'evento': evento}
    html_mensagem = render_to_string('emails/evento_solicitacao_recebida.html', contexto)
    
    # Texto simples para clientes de email que não suportam HTML
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
    
    return enviar_email_async(
        assunto,
        mensagem,
        email_de,
        email_para,
        html_message=html_mensagem
    )

def enviar_email_solicitacao_aprovada(evento):
    """
    Envia um email notificando que a solicitação de evento/visita foi aprovada.
    
    Args:
        evento: O objeto Event que foi aprovado
    """
    usuario = evento.created_by
    assunto = f'Solicitação aprovada - {evento.title}'
    
    # Criar conteúdo do email em HTML
    contexto = {'evento': evento}
    html_mensagem = render_to_string('emails/evento_solicitacao_aprovada.html', contexto)
    
    # Texto simples para clientes de email que não suportam HTML
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
    
    return enviar_email_async(
        assunto,
        mensagem,
        email_de,
        email_para,
        html_message=html_mensagem
    )

def enviar_email_solicitacao_recusada(evento, motivo):
    """
    Envia um email notificando que a solicitação de evento/visita foi recusada.
    
    Args:
        evento: O objeto Event que foi recusado
        motivo: O motivo da recusa
    """
    usuario = evento.created_by
    assunto = f'Solicitação recusada - {evento.title}'
    
    # Criar conteúdo do email em HTML
    contexto = {'evento': evento, 'motivo': motivo}
    html_mensagem = render_to_string('emails/evento_solicitacao_recusada.html', contexto)
    
    # Texto simples para clientes de email que não suportam HTML
    mensagem = f"""
    Olá {usuario.first_name} {usuario.last_name},
    
    Infelizmente sua solicitação para o evento "{evento.title}" foi recusada.
    
    Detalhes da solicitação:
    - Tipo: {evento.get_event_type_display()}
    - Data: {evento.start_time.strftime('%d/%m/%Y')}
    - Horário: {evento.start_time.strftime('%H:%M')} - {evento.end_time.strftime('%H:%M')}
    
    Motivo da recusa:
    {motivo}
    
    Se tiver dúvidas, entre em contato conosco para mais informações.
    
    Atenciosamente,
    Equipe do Sistema de Gestão do Laboratório
    """
    
    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]
    
    return enviar_email_async(
        assunto,
        mensagem,
        email_de,
        email_para,
        html_message=html_mensagem
    )

def enviar_email_notificacao_interesse(solicitacao):
    """
    Envia uma notificação por e-mail quando alguém demonstra interesse em uma capacidade do laboratório.
    
    Args:
        solicitacao: O objeto SolicitacaoInteresse que foi criado
    """
    assunto = f"Nova solicitação de interesse: {solicitacao.servico.nome}"
    
    # Criar conteúdo do email em HTML
    contexto = {
        'solicitacao': solicitacao,
        'servico': solicitacao.servico,
    }
    html_mensagem = render_to_string('emails/novo_interesse.html', contexto)
    
    # Texto simples para clientes de email que não suportam HTML
    texto_mensagem = f"""
    Nova solicitação de interesse no FabLab:
    
    Capacidade: {solicitacao.servico.nome}
    Nome: {solicitacao.nome}
    Email: {solicitacao.email}
    Telefone: {solicitacao.telefone or "Não informado"}
    
    Descrição do projeto/interesse:
    {solicitacao.descricao_projeto}
    
    ---
    Este é um email automático enviado pelo sistema do FabLab IFMT.
    """
    
    # Email de quem envia
    email_de = settings.DEFAULT_FROM_EMAIL
    
    # Email para onde vai a notificação
    email_para = ['ifmtmaker.fablab.cba@gmail.com']
    
    return enviar_email_async(
        assunto,
        texto_mensagem,
        email_de,
        email_para,
        html_message=html_mensagem
    )
