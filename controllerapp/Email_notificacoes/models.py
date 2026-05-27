from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from .utils import enviar_email_async


def _site_url():
    """Retorna a URL pública do sistema definida em settings.SITE_URL."""
    return getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')

def enviar_email_boas_vindas(usuario):
    """
    Envia um email de boas-vindas para o novo usuário registrado.
    
    Args:
        usuario: O objeto usuário que acabou de se registrar
    """
    assunto = f'Bem-vindo(a) ao Sistema de Gestão do Laboratório, {usuario.first_name}!'
    
    # Criar conteúdo do email em HTML
    site_url = _site_url()
    contexto = {'usuario': usuario, 'site_url': site_url}
    html_mensagem = render_to_string('emails/boas_vindas.html', contexto)

    # Texto simples para clientes de email que não suportam HTML
    mensagem = (
        f"Olá {usuario.first_name} {usuario.last_name},\n\n"
        f"Seja bem-vindo(a) ao Sistema de Gestão do FabLab IFMT!\n\n"
        f"Seu cadastro foi realizado com sucesso. Agora você pode acessar todas as funcionalidades disponíveis para o seu perfil.\n\n"
        f"Seus dados de acesso:\n"
        f"  Matrícula: {usuario.id}\n"
        f"  Email: {usuario.email}\n\n"
        f"Acesse o sistema: {site_url}/\n\n"
        f"Em caso de dúvidas, entre em contato conosco.\n\n"
        f"Atenciosamente,\nEquipe FabLab IFMT"
    )
    
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
    site_url = _site_url()
    contexto = {'evento': evento, 'site_url': site_url}
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
    site_url = _site_url()
    contexto = {'evento': evento, 'site_url': site_url}
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
    site_url = _site_url()
    contexto = {'evento': evento, 'motivo': motivo, 'site_url': site_url}
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


def enviar_email_confirmacao(usuario, confirm_link):
    """
    Envia email de confirmação de endereço para o usuário recém-cadastrado.

    Args:
        usuario: O objeto usuário que se cadastrou
        confirm_link: URL completa para confirmação do email
    """
    assunto = 'Confirme seu email - FabLab IFMT'

    contexto = {'usuario': usuario, 'confirm_link': confirm_link}
    html_mensagem = render_to_string('users/email_confirm.html', contexto)

    mensagem = (
        f"Olá {usuario.first_name} {usuario.last_name},\n\n"
        f"Obrigado por se cadastrar no Sistema de Gestão do FabLab IFMT!\n\n"
        f"Por favor, confirme seu email clicando no link abaixo:\n"
        f"{confirm_link}\n\n"
        f"Este link é válido por 3 dias.\n\n"
        f"Se você não criou esta conta, ignore este email.\n\n"
        f"Atenciosamente,\nEquipe FabLab IFMT"
    )

    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]

    return enviar_email_async(assunto, mensagem, email_de, email_para, html_message=html_mensagem)


def enviar_email_confirmacao_exclusao(usuario, confirm_link):
    """
    Envia email de confirmação antes de concluir a exclusão/anonimização da conta (Art. 17 LGPD).

    Args:
        usuario: O objeto usuário que solicitou a exclusão
        confirm_link: URL assinada para confirmar a exclusão (válida por 24 h)
    """
    assunto = 'Confirme a exclusão da sua conta - FabLab IFMT'

    contexto = {'usuario': usuario, 'confirm_link': confirm_link}
    html_mensagem = render_to_string('emails/lgpd_exclusao_confirmacao.html', contexto)

    mensagem = (
        f"Olá {usuario.first_name} {usuario.last_name},\n\n"
        f"Recebemos uma solicitação para EXCLUIR permanentemente sua conta no FabLab IFMT.\n\n"
        f"Se você realmente deseja excluir sua conta, clique no link abaixo:\n"
        f"{confirm_link}\n\n"
        f"ATENÇÃO: esta ação é irreversível. Todos os seus dados pessoais serão anonimizados.\n"
        f"O link é válido por 24 horas.\n\n"
        f"Se você NÃO solicitou esta exclusão, ignore este email. "
        f"Sua conta permanece ativa e segura.\n\n"
        f"Atenciosamente,\nEquipe FabLab IFMT"
    )

    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]

    return enviar_email_async(assunto, mensagem, email_de, email_para, html_message=html_mensagem)


def enviar_email_redefinicao_senha(usuario, reset_url):
    """
    Envia email de redefinição de senha para o usuário.

    Args:
        usuario: O objeto usuário que solicitou a redefinição
        reset_url: URL completa para redefinição da senha
    """
    assunto = 'Redefinição de senha - FabLab IFMT'

    contexto = {
        'user': usuario,
        'usuario': usuario,
        'email': usuario.email,
        'reset_url': reset_url,
        'site_name': 'FabLab IFMT',
    }
    html_mensagem = render_to_string('users/password_reset_email.html', contexto)

    mensagem = (
        f"Olá {usuario.first_name} {usuario.last_name},\n\n"
        f"Recebemos uma solicitação para redefinir a senha da sua conta no FabLab IFMT.\n\n"
        f"Clique no link abaixo para criar uma nova senha:\n"
        f"{reset_url}\n\n"
        f"Este link é válido por 24 horas.\n\n"
        f"Se você não solicitou a redefinição de senha, ignore este email. "
        f"Sua senha permanece a mesma.\n\n"
        f"Atenciosamente,\nEquipe FabLab IFMT"
    )

    email_de = settings.DEFAULT_FROM_EMAIL
    email_para = [usuario.email]

    return enviar_email_async(assunto, mensagem, email_de, email_para, html_message=html_mensagem)
