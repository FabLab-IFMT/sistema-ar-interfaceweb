from django.test import TestCase
from django.utils.text import slugify
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# Noticia — model
# ---------------------------------------------------------------------------

class NoticiaModelTest(TestCase):

    def _criar_noticia(self, titulo='Notícia Teste', **kwargs):
        from options.models import Noticia
        defaults = {
            'titulo': titulo,
            'slug': slugify(titulo),
            'resumo': 'Resumo curto',
            'conteudo': 'Conteúdo completo.',
            'publicado': True,
        }
        defaults.update(kwargs)
        return Noticia.objects.create(**defaults)

    def test_str_retorna_titulo(self):
        n = self._criar_noticia('Minha Notícia')
        self.assertEqual(str(n), 'Minha Notícia')

    def test_get_absolute_url_contem_slug(self):
        n = self._criar_noticia('Noticia De Teste')
        self.assertIn('noticia-de-teste', n.get_absolute_url())


# ---------------------------------------------------------------------------
# Noticia — API
# ---------------------------------------------------------------------------

class NoticiaAPITest(APITestCase):

    def setUp(self):
        from options.models import Noticia
        self.admin = create_superuser()
        self.user = create_user()
        Noticia.objects.create(
            titulo='Notícia Pública', slug='noticia-publica',
            resumo='Resumo', conteudo='Conteúdo', publicado=True,
        )
        Noticia.objects.create(
            titulo='Notícia Oculta', slug='noticia-oculta',
            resumo='Resumo', conteudo='Conteúdo', publicado=False,
        )

    def test_listagem_publica_sem_autenticacao(self):
        resp = self.client.get('/api/noticias/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_detalhe_por_slug(self):
        resp = self.client.get('/api/noticias/noticia-publica/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_usuario_nao_admin_nao_pode_criar(self):
        payload = {'titulo': 'Nova', 'slug': 'nova', 'resumo': 'R', 'conteudo': 'C'}
        resp = auth_client(self.user).post('/api/noticias/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_sem_auth_nao_pode_criar(self):
        payload = {'titulo': 'Nova', 'slug': 'nova', 'resumo': 'R', 'conteudo': 'C'}
        resp = self.client.post('/api/noticias/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# Servico — model
# ---------------------------------------------------------------------------

class ServicoModelTest(TestCase):

    def setUp(self):
        from options.models import CategoriaServico, Servico
        cat = CategoriaServico.objects.create(nome='Corte a Laser', icone='fa-cut', ordem=1)
        self.servico = Servico.objects.create(
            categoria=cat,
            nome='Corte Laser',
            descricao_curta='Corte preciso',
            descricao='Detalhes do serviço',
            como_utilizar='Passo 1\nPasso 2\nPasso 3',
            aplicacoes='App 1\nApp 2',
        )

    def test_get_como_utilizar_list_retorna_lista_correta(self):
        self.assertEqual(self.servico.get_como_utilizar_list(), ['Passo 1', 'Passo 2', 'Passo 3'])

    def test_get_aplicacoes_list_retorna_lista_correta(self):
        self.assertEqual(self.servico.get_aplicacoes_list(), ['App 1', 'App 2'])

    def test_como_utilizar_vazio_retorna_lista_vazia(self):
        self.servico.como_utilizar = ''
        self.assertEqual(self.servico.get_como_utilizar_list(), [])


# ---------------------------------------------------------------------------
# Servico — API
# ---------------------------------------------------------------------------

class ServicoAPITest(APITestCase):

    def setUp(self):
        from options.models import CategoriaServico, Servico
        self.admin = create_superuser()
        self.user = create_user()
        cat = CategoriaServico.objects.create(nome='Impressão 3D', icone='fa-print', ordem=1)
        self.servico = Servico.objects.create(
            categoria=cat, nome='Impressão PLA',
            descricao_curta='Impressão em PLA',
            descricao='Descrição completa',
            disponivel=True,
        )

    def test_listagem_de_servicos_e_publica(self):
        resp = self.client.get('/api/servicos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_detalhe_de_servico(self):
        resp = self.client.get(f'/api/servicos/{self.servico.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nome'], 'Impressão PLA')

    def test_usuario_comum_nao_pode_criar_servico(self):
        payload = {'nome': 'Novo', 'descricao_curta': 'x', 'descricao': 'y'}
        resp = auth_client(self.user).post('/api/servicos/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# SolicitacaoInteresse — API
# ---------------------------------------------------------------------------

class SolicitacaoAPITest(APITestCase):

    def setUp(self):
        from options.models import CategoriaServico, Servico
        cat = CategoriaServico.objects.create(nome='Cat', icone='fa-gear', ordem=1)
        self.servico = Servico.objects.create(
            categoria=cat, nome='Svc', descricao_curta='x', descricao='y',
        )

    def test_criar_solicitacao_e_publico(self):
        payload = {
            'nome': 'João Aluno',
            'email': 'joao@test.com',
            'servico': self.servico.pk,
            'descricao_projeto': 'Quero imprimir meu projeto de TCC.',
        }
        resp = self.client.post('/api/solicitacoes-interesse/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

    def test_listar_solicitacoes_requer_autenticacao(self):
        resp = self.client.get('/api/solicitacoes-interesse/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# Membro — API
# ---------------------------------------------------------------------------

class MembroAPITest(APITestCase):

    def setUp(self):
        from options.models import Membro
        Membro.objects.create(nome='Ana Silva', cargo='Técnica', ativo=True, ordem=1)
        self.admin = create_superuser()

    def test_listagem_de_membros_e_publica(self):
        resp = self.client.get('/api/membros/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_usuario_nao_staff_nao_pode_criar_membro(self):
        user = create_user('55544433322')
        resp = auth_client(user).post('/api/membros/', {'nome': 'X', 'cargo': 'Y'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Hashtag — model
# ---------------------------------------------------------------------------

class HashtagModelTest(TestCase):

    def test_slug_gerado_automaticamente(self):
        from options.models import Hashtag
        tag = Hashtag.objects.create(nome='Impressão 3D')
        self.assertEqual(tag.slug, 'impressao-3d')

    def test_str_retorna_nome_com_hash(self):
        from options.models import Hashtag
        tag = Hashtag.objects.create(nome='FabLab', slug='fablab')
        self.assertEqual(str(tag), '#FabLab')
