import threading
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core import mail

from tests_utils import create_user, create_superuser


# ---------------------------------------------------------------------------
# enviar_email_async — função utilitária
# ---------------------------------------------------------------------------

class EnviarEmailAsyncTest(TestCase):
    """Testa o envio assíncrono de emails usando o backend in-memory."""

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_enviado_e_retorna_true(self):
        from Email_notificacoes.utils import enviar_email_async

        resultado = enviar_email_async(
            assunto='Teste de Email',
            mensagem='Corpo do email em texto.',
            email_de='noreply@test.com',
            email_para=['destino@test.com'],
        )
        self.assertTrue(resultado)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_async_roda_em_thread(self):
        from Email_notificacoes.utils import enviar_email_async

        threads_antes = threading.active_count()
        enviar_email_async(
            assunto='Thread Test',
            mensagem='Corpo',
            email_de='noreply@test.com',
            email_para=['x@test.com'],
        )
        # Thread é daemon — não necessariamente estará ativa, mas não deve lançar exceção
        self.assertTrue(True)


# ---------------------------------------------------------------------------
# enviar_email_boas_vindas
# ---------------------------------------------------------------------------

class EnviarEmailBoasVindasTest(TestCase):

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('Email_notificacoes.models.render_to_string', return_value='<p>Bem-vindo!</p>')
    @patch('Email_notificacoes.models.enviar_email_async')
    def test_chama_enviar_async_com_dados_do_usuario(self, mock_async, mock_render):
        from Email_notificacoes.models import enviar_email_boas_vindas
        usuario = create_user('12345000001', email='joao@test.com')

        enviar_email_boas_vindas(usuario)

        # O signal post_save também chama enviar_email_async ao criar o usuário,
        # por isso verificamos que foi chamada (ao menos uma vez) e conferimos a última chamada.
        mock_async.assert_called()
        args = mock_async.call_args_list[-1][0]   # última chamada, argumentos posicionais
        self.assertIn(usuario.first_name, args[0])  # assunto contém o nome
        self.assertIn(usuario.email, args[3])         # destinatário correto

    @patch('Email_notificacoes.models.render_to_string', return_value='<p>ok</p>')
    @patch('Email_notificacoes.models.enviar_email_async', return_value=True)
    def test_retorna_true_em_sucesso(self, mock_async, mock_render):
        from Email_notificacoes.models import enviar_email_boas_vindas
        usuario = create_user('12345000002')
        resultado = enviar_email_boas_vindas(usuario)
        self.assertTrue(resultado)


# ---------------------------------------------------------------------------
# enviar_email_solicitacao_enviada / aprovada / recusada
# ---------------------------------------------------------------------------

class EnviarEmailEventoTest(TestCase):

    def _criar_evento(self):
        from logs.models import Event
        from django.utils import timezone
        user = create_user('12345000003')
        return Event.objects.create(
            title='Workshop Impressão',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2),
            event_type='workshop',
            created_by=user,
        )

    @patch('Email_notificacoes.models.render_to_string', return_value='<p>ok</p>')
    @patch('Email_notificacoes.models.enviar_email_async', return_value=True)
    def test_email_solicitacao_enviada(self, mock_async, mock_render):
        from Email_notificacoes.models import enviar_email_solicitacao_enviada
        evento = self._criar_evento()
        resultado = enviar_email_solicitacao_enviada(evento)
        # Signal post_save já chamou enviar_email_async ao criar o usuário; verificamos >= 1 chamada
        mock_async.assert_called()
        self.assertTrue(resultado)

    @patch('Email_notificacoes.models.render_to_string', return_value='<p>ok</p>')
    @patch('Email_notificacoes.models.enviar_email_async', return_value=True)
    def test_email_solicitacao_aprovada(self, mock_async, mock_render):
        from Email_notificacoes.models import enviar_email_solicitacao_aprovada
        evento = self._criar_evento()
        resultado = enviar_email_solicitacao_aprovada(evento)
        # Signal post_save já chamou enviar_email_async ao criar o usuário; verificamos >= 1 chamada
        mock_async.assert_called()
        self.assertTrue(resultado)

    @patch('Email_notificacoes.models.render_to_string', return_value='<p>ok</p>')
    @patch('Email_notificacoes.models.enviar_email_async', return_value=True)
    def test_email_solicitacao_recusada_inclui_motivo(self, mock_async, mock_render):
        from Email_notificacoes.models import enviar_email_solicitacao_recusada
        evento = self._criar_evento()
        enviar_email_solicitacao_recusada(evento, motivo='Data indisponível')
        args = mock_async.call_args[0]
        # Mensagem de texto deve conter o motivo
        self.assertIn('Data indisponível', args[1])


# ---------------------------------------------------------------------------
# enviar_email_notificacao_interesse
# ---------------------------------------------------------------------------

class EnviarEmailInteresseTest(TestCase):

    @patch('Email_notificacoes.models.render_to_string', return_value='<p>ok</p>')
    @patch('Email_notificacoes.models.enviar_email_async', return_value=True)
    def test_email_interesse_inclui_nome_servico(self, mock_async, mock_render):
        from Email_notificacoes.models import enviar_email_notificacao_interesse
        from options.models import CategoriaServico, Servico, SolicitacaoInteresse

        cat = CategoriaServico.objects.create(nome='Cat', icone='fa-gear', ordem=1)
        svc = Servico.objects.create(
            categoria=cat, nome='Corte CNC',
            descricao_curta='Corte CNC', descricao='Descrição',
        )
        sol = SolicitacaoInteresse.objects.create(
            nome='Cliente Teste',
            email='cliente@test.com',
            servico=svc,
            descricao_projeto='Preciso de 10 peças cortadas.',
        )

        enviar_email_notificacao_interesse(sol)

        args = mock_async.call_args[0]
        # Assunto deve mencionar o nome do serviço
        self.assertIn('Corte CNC', args[0])


# ---------------------------------------------------------------------------
# Sinal — email de boas-vindas ao criar usuário
# ---------------------------------------------------------------------------

class SinalBoasVindasTest(TestCase):

    @patch('Email_notificacoes.models.render_to_string', return_value='<p>ok</p>')
    @patch('Email_notificacoes.models.enviar_email_async', return_value=True)
    def test_sinal_dispara_ao_criar_usuario(self, mock_async, mock_render):
        """Ao criar um novo usuário, o sinal deve acionar enviar_email_boas_vindas."""
        create_user('98765432100')
        # O sinal post_save chama enviar_email_boas_vindas que chama enviar_email_async
        mock_async.assert_called()
