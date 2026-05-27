from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# KanbanColumn — model
# ---------------------------------------------------------------------------

class KanbanColumnModelTest(TestCase):

    def test_criacao_de_coluna(self):
        from canva.models import KanbanColumn
        col = KanbanColumn.objects.create(nome='A Fazer', ordem=1, cor='#f0f0f0')
        self.assertEqual(str(col), 'A Fazer')

    def test_ordenacao_por_campo_ordem(self):
        from canva.models import KanbanColumn
        KanbanColumn.objects.create(nome='Terceira', ordem=3)
        KanbanColumn.objects.create(nome='Primeira', ordem=1)
        KanbanColumn.objects.create(nome='Segunda', ordem=2)
        nomes = list(KanbanColumn.objects.values_list('nome', flat=True))
        self.assertEqual(nomes, ['Primeira', 'Segunda', 'Terceira'])


# ---------------------------------------------------------------------------
# KanbanCard — model
# ---------------------------------------------------------------------------

class KanbanCardModelTest(TestCase):

    def setUp(self):
        from canva.models import KanbanColumn
        self.user = create_user()
        self.coluna = KanbanColumn.objects.create(nome='Em Progresso', ordem=2)

    def test_criacao_de_card(self):
        from canva.models import KanbanCard
        card = KanbanCard.objects.create(
            titulo='Implementar autenticação',
            descricao='JWT com SimpleJWT',
            coluna=self.coluna,
            prioridade='alta',
            criado_por=self.user,
        )
        self.assertEqual(str(card), 'Implementar autenticação')

    def test_prioridade_padrao_e_media(self):
        from canva.models import KanbanCard
        card = KanbanCard.objects.create(
            titulo='Tarefa Simples',
            coluna=self.coluna,
            criado_por=self.user,
        )
        self.assertEqual(card.prioridade, 'media')

    def test_progresso_padrao_e_zero(self):
        from canva.models import KanbanCard
        card = KanbanCard.objects.create(
            titulo='Progresso Zero',
            coluna=self.coluna,
        )
        self.assertEqual(card.progresso, 0)


# ---------------------------------------------------------------------------
# KanbanColumn — API
# ---------------------------------------------------------------------------

class KanbanColumnAPITest(APITestCase):

    def setUp(self):
        from canva.models import KanbanColumn
        self.admin = create_superuser()
        self.user = create_user()
        self.col1 = KanbanColumn.objects.create(nome='Backlog', ordem=1)
        self.col2 = KanbanColumn.objects.create(nome='Concluído', ordem=3)

    def test_listar_colunas_requer_autenticacao(self):
        resp = self.client.get('/api/kanban-columns/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_usuario_autenticado_pode_listar_colunas(self):
        resp = auth_client(self.user).get('/api/kanban-columns/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_coluna(self):
        payload = {'nome': 'Revisão', 'ordem': 2, 'cor': '#ffcc00'}
        resp = auth_client(self.user).post('/api/kanban-columns/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

    def test_deletar_coluna_requer_autenticacao(self):
        resp = self.client.delete(f'/api/kanban-columns/{self.col1.pk}/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# KanbanCard — API
# ---------------------------------------------------------------------------

class KanbanCardAPITest(APITestCase):

    def setUp(self):
        from canva.models import KanbanColumn, KanbanCard
        self.user = create_user()
        self.admin = create_superuser()
        self.col_origem = KanbanColumn.objects.create(nome='A Fazer', ordem=1)
        self.col_destino = KanbanColumn.objects.create(nome='Feito', ordem=2)
        self.card = KanbanCard.objects.create(
            titulo='Tarefa API',
            coluna=self.col_origem,
            prioridade='media',
            criado_por=self.user,
        )

    def test_listar_cards_requer_autenticacao(self):
        resp = self.client.get('/api/kanban-cards/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_usuario_autenticado_pode_listar_cards(self):
        resp = auth_client(self.user).get('/api/kanban-cards/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_card(self):
        payload = {
            'titulo': 'Novo Card',
            'coluna': self.col_origem.pk,
            'prioridade': 'alta',
        }
        resp = auth_client(self.user).post('/api/kanban-cards/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

    def test_mover_card_para_outra_coluna(self):
        payload = {'coluna': self.col_destino.pk}
        resp = auth_client(self.user).post(
            f'/api/kanban-cards/{self.card.pk}/move/', payload, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.card.refresh_from_db()
        self.assertEqual(self.card.coluna, self.col_destino)

    def test_atualizar_progresso_do_card(self):
        resp = auth_client(self.user).patch(
            f'/api/kanban-cards/{self.card.pk}/', {'progresso': 75}, format='json'
        )
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))
        self.card.refresh_from_db()
        self.assertEqual(self.card.progresso, 75)
