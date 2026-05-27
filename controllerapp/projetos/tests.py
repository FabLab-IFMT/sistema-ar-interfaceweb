from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# Projeto — model
# ---------------------------------------------------------------------------

class ProjetoModelTest(TestCase):

    def _criar_projeto(self, titulo='Projeto Alpha', **kwargs):
        from projetos.models import Projeto
        defaults = {
            'titulo': titulo,
            'descricao_curta': 'Resumo do projeto',
            'descricao': 'Descrição completa do projeto Alpha.',
            'data_inicio': date.today(),
            'status': 'em_andamento',
            'publicado': True,
        }
        defaults.update(kwargs)
        return Projeto.objects.create(**defaults)

    def test_slug_gerado_automaticamente(self):
        p = self._criar_projeto('Impressora 3D FabLab')
        self.assertIn('impressora', p.slug)

    def test_slug_unico_para_titulos_duplicados(self):
        p1 = self._criar_projeto('Projeto Drone')
        p2 = self._criar_projeto('Projeto Drone')
        self.assertNotEqual(p1.slug, p2.slug)

    def test_str_retorna_titulo(self):
        p = self._criar_projeto('Robô Educacional')
        self.assertEqual(str(p), 'Robô Educacional')

    def test_get_absolute_url_contem_slug(self):
        p = self._criar_projeto('Projeto Web')
        self.assertIn(p.slug, p.get_absolute_url())


# ---------------------------------------------------------------------------
# ProjetoTag — model
# ---------------------------------------------------------------------------

class ProjetoTagModelTest(TestCase):

    def test_slug_gerado_automaticamente(self):
        from projetos.models import ProjetoTag
        tag = ProjetoTag.objects.create(nome='Impressão 3D')
        self.assertEqual(tag.slug, 'impressao-3d')


# ---------------------------------------------------------------------------
# Projeto — API
# ---------------------------------------------------------------------------

class ProjetoAPITest(APITestCase):

    def setUp(self):
        from projetos.models import Projeto
        self.admin = create_superuser()
        self.user = create_user()
        self.projeto = Projeto.objects.create(
            titulo='Projeto Público',
            descricao_curta='Resumo',
            descricao='Descrição longa',
            data_inicio=date.today(),
            status='em_andamento',
            publicado=True,
        )

    def test_listagem_publica(self):
        resp = self.client.get('/api/projetos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_detalhe_por_slug(self):
        resp = self.client.get(f'/api/projetos/{self.projeto.slug}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['titulo'], 'Projeto Público')

    def test_usuario_autenticado_nao_pode_criar_projeto(self):
        payload = {
            'titulo': 'Novo', 'descricao_curta': 'x', 'descricao': 'y',
            'data_inicio': str(date.today()), 'status': 'planejado'
        }
        resp = auth_client(self.user).post('/api/projetos/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# ComentarioProjeto — API
# ---------------------------------------------------------------------------

class ComentarioProjetoAPITest(APITestCase):

    def setUp(self):
        from projetos.models import Projeto
        self.user = create_user()
        self.projeto = Projeto.objects.create(
            titulo='Proj Comentado',
            descricao_curta='x', descricao='y',
            data_inicio=date.today(), publicado=True,
        )

    def test_criar_comentario_autenticado(self):
        payload = {'projeto': self.projeto.pk, 'texto': 'Que projeto incrível!'}
        resp = auth_client(self.user).post('/api/comentarios-projeto/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_comentario_sem_autenticacao_e_negado(self):
        payload = {'projeto': self.projeto.pk, 'texto': 'Tentativa anônima'}
        resp = self.client.post('/api/comentarios-projeto/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_resposta_aninhada_a_comentario(self):
        from projetos.models import ComentarioProjeto
        pai = ComentarioProjeto.objects.create(
            projeto=self.projeto, autor=self.user, texto='Comentário principal'
        )
        payload = {
            'projeto': self.projeto.pk,
            'texto': 'Resposta ao comentário',
            'comentario_pai': pai.pk,
        }
        resp = auth_client(self.user).post('/api/comentarios-projeto/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# TodoTask — API
# ---------------------------------------------------------------------------

class TodoTaskAPITest(APITestCase):

    def setUp(self):
        self.user = create_user()
        self.admin = create_superuser()

    def test_criar_tarefa_autenticado(self):
        payload = {'titulo': 'Revisão de código', 'prioridade': 'alta'}
        resp = auth_client(self.user).post('/api/todo-tasks/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_listagem_retorna_apenas_tarefas_do_usuario(self):
        from projetos.models import TodoTask
        outro_user = create_superuser('88877766655')
        TodoTask.objects.create(titulo='Tarefa Minha', usuario=self.user, prioridade='baixa')
        TodoTask.objects.create(titulo='Tarefa Alheia', usuario=outro_user, prioridade='baixa')
        resp = auth_client(self.user).get('/api/todo-tasks/')
        titulos = [t['titulo'] for t in resp.data.get('results', resp.data)]
        self.assertIn('Tarefa Minha', titulos)

    def test_sem_autenticacao_nao_acessa_tarefas(self):
        resp = self.client.get('/api/todo-tasks/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# TodoTask — model
# ---------------------------------------------------------------------------

class TodoTaskModelTest(TestCase):

    def setUp(self):
        from projetos.models import TodoTask
        self.user = create_user('44455566677')
        self.task_atrasada = TodoTask.objects.create(
            titulo='Urgente',
            data_limite=date.today() - timedelta(days=3),
            concluida=False,
            usuario=self.user,
        )
        self.task_no_prazo = TodoTask.objects.create(
            titulo='No Prazo',
            data_limite=date.today() + timedelta(days=5),
            concluida=False,
            usuario=self.user,
        )

    def test_esta_atrasada_quando_vencida(self):
        self.assertTrue(self.task_atrasada.esta_atrasada)

    def test_nao_esta_atrasada_quando_no_prazo(self):
        self.assertFalse(self.task_no_prazo.esta_atrasada)

    def test_dias_restantes_positivo_para_futuro(self):
        self.assertGreater(self.task_no_prazo.dias_restantes, 0)
