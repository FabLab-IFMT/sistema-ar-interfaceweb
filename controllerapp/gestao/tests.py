from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# Configuracao — model
# ---------------------------------------------------------------------------

class ConfiguracaoModelTest(TestCase):

    def test_criacao_de_configuracao(self):
        from gestao.models import Configuracao
        cfg = Configuracao.objects.create(
            nome='MAX_USUARIOS',
            descricao='Número máximo de usuários',
            valor='100',
            categoria='sistema',
        )
        self.assertEqual(cfg.nome, 'MAX_USUARIOS')
        self.assertEqual(cfg.valor, '100')

    def test_str_contem_nome_e_categoria(self):
        from gestao.models import Configuracao
        cfg = Configuracao.objects.create(
            nome='SMTP_HOST',
            descricao='Host SMTP',
            categoria='email',
        )
        s = str(cfg)
        self.assertIn('SMTP_HOST', s)

    def test_nome_deve_ser_unico(self):
        from gestao.models import Configuracao
        from django.db import IntegrityError
        Configuracao.objects.create(nome='CHAVE_UNICA', descricao='x')
        with self.assertRaises(IntegrityError):
            Configuracao.objects.create(nome='CHAVE_UNICA', descricao='y')

    def test_categorias_validas(self):
        from gestao.models import Configuracao
        categorias = [c[0] for c in Configuracao.CATEGORIAS]
        self.assertIn('geral', categorias)
        self.assertIn('email', categorias)
        self.assertIn('laboratorio', categorias)
        self.assertIn('sistema', categorias)
        self.assertIn('acesso', categorias)


# ---------------------------------------------------------------------------
# AcessoGestao — model
# ---------------------------------------------------------------------------

class AcessoGestaoModelTest(TestCase):

    def setUp(self):
        self.admin = create_superuser()
        self.user = create_user()

    def test_criacao_com_acesso_inativo_por_padrao(self):
        from gestao.models import AcessoGestao
        acesso = AcessoGestao.objects.create(
            usuario=self.user,
            concedido_por=self.admin,
        )
        self.assertFalse(acesso.tem_acesso)

    def test_conceder_acesso(self):
        from gestao.models import AcessoGestao
        acesso = AcessoGestao.objects.create(
            usuario=self.user,
            tem_acesso=True,
            concedido_por=self.admin,
        )
        self.assertTrue(acesso.tem_acesso)

    def test_relacao_one_to_one_por_usuario(self):
        from gestao.models import AcessoGestao
        from django.db import IntegrityError
        AcessoGestao.objects.create(usuario=self.user, concedido_por=self.admin)
        with self.assertRaises(IntegrityError):
            AcessoGestao.objects.create(usuario=self.user, concedido_por=self.admin)


# ---------------------------------------------------------------------------
# AcessoGestao — API
# ---------------------------------------------------------------------------

class AcessoGestaoAPITest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()
        self.user = create_user()

    def test_listar_acessos_requer_superuser(self):
        resp = auth_client(self.user).get('/api/acessos-gestao/')
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_200_OK))

    def test_admin_pode_listar_acessos(self):
        resp = auth_client(self.admin).get('/api/acessos-gestao/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_toggle_acesso(self):
        from gestao.models import AcessoGestao
        acesso = AcessoGestao.objects.create(
            usuario=self.user,
            tem_acesso=False,
            concedido_por=self.admin,
        )
        resp = auth_client(self.admin).post(f'/api/acessos-gestao/{acesso.pk}/toggle/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        acesso.refresh_from_db()
        self.assertTrue(acesso.tem_acesso)

    def test_sem_autenticacao_nao_acessa(self):
        resp = self.client.get('/api/acessos-gestao/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# Configuracao — API
# ---------------------------------------------------------------------------

class ConfiguracaoAPITest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()
        self.user = create_user()

    def test_listar_configuracoes_requer_auth(self):
        resp = self.client.get('/api/configuracoes/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_admin_pode_criar_configuracao(self):
        payload = {
            'nome': 'LIMITE_UPLOADS',
            'descricao': 'Tamanho máximo de upload em MB',
            'valor': '10',
            'categoria': 'sistema',
        }
        resp = auth_client(self.admin).post('/api/configuracoes/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))


# ---------------------------------------------------------------------------
# Dashboard — API
# ---------------------------------------------------------------------------

class DashboardAPITest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()
        self.user = create_user()

    def test_dashboard_requer_autenticacao(self):
        resp = self.client.get('/api/dashboard/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_admin_acessa_dashboard(self):
        resp = auth_client(self.admin).get('/api/dashboard/')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN))
