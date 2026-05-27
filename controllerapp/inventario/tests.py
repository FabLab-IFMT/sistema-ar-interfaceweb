from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# Item — model
# ---------------------------------------------------------------------------

class ItemModelTest(TestCase):

    def setUp(self):
        from inventario.models import Categoria, Item
        cat = Categoria.objects.create(nome='Filamentos')
        self.item = Item.objects.create(
            nome='PLA 1kg',
            categoria=cat,
            quantidade=Decimal('5'),
            quantidade_minima=Decimal('10'),
            valor_unitario=Decimal('80.00'),
        )

    def test_codigo_gerado_automaticamente_com_prefixo_fab(self):
        self.assertTrue(self.item.codigo.startswith('FAB-'))

    def test_estoque_baixo_quando_quantidade_menor_que_minimo(self):
        self.assertTrue(self.item.estoque_baixo)

    def test_estoque_nao_baixo_acima_do_minimo(self):
        self.item.quantidade = Decimal('20')
        self.item.save()
        self.assertFalse(self.item.estoque_baixo)

    def test_valor_total_calculado_corretamente(self):
        self.assertEqual(self.item.valor_total, Decimal('5') * Decimal('80.00'))

    def test_valor_total_none_quando_sem_preco(self):
        self.item.valor_unitario = None
        self.item.save()
        self.assertIsNone(self.item.valor_total)

    def test_str_contem_nome_e_codigo(self):
        s = str(self.item)
        self.assertIn('PLA 1kg', s)
        self.assertIn('FAB-', s)


# ---------------------------------------------------------------------------
# Emprestimo — model
# ---------------------------------------------------------------------------

class EmprestimoModelTest(TestCase):

    def setUp(self):
        from inventario.models import Categoria, Item, Emprestimo
        self.user = create_user()
        self.admin = create_superuser()
        cat = Categoria.objects.create(nome='Ferramentas')
        self.item = Item.objects.create(
            nome='Chave de Fenda', categoria=cat, quantidade=Decimal('3'),
        )
        self.emp_ativo = Emprestimo.objects.create(
            item=self.item, usuario=self.user, quantidade=Decimal('1'),
            data_prevista_devolucao=timezone.now() + timedelta(days=3),
            responsavel_emprestimo=self.admin,
        )
        self.emp_atrasado = Emprestimo.objects.create(
            item=self.item, usuario=self.user, quantidade=Decimal('1'),
            data_prevista_devolucao=timezone.now() - timedelta(days=2),
            responsavel_emprestimo=self.admin,
        )

    def test_status_emprestado_quando_dentro_do_prazo(self):
        self.assertEqual(self.emp_ativo.status, 'emprestado')

    def test_status_atrasado_quando_fora_do_prazo(self):
        self.assertEqual(self.emp_atrasado.status, 'atrasado')

    def test_status_devolvido_quando_data_devolucao_preenchida(self):
        self.emp_ativo.data_devolucao = timezone.now()
        self.emp_ativo.save()
        self.assertEqual(self.emp_ativo.status, 'devolvido')


# ---------------------------------------------------------------------------
# Item — API
# ---------------------------------------------------------------------------

class ItemAPITest(APITestCase):

    def setUp(self):
        from inventario.models import Categoria, Item
        self.admin = create_superuser()
        self.user = create_user()
        cat = Categoria.objects.create(nome='Eletrônicos')
        Item.objects.create(
            nome='Arduino Uno', categoria=cat,
            quantidade=Decimal('2'), quantidade_minima=Decimal('5'),
        )
        Item.objects.create(
            nome='Raspberry Pi', categoria=cat,
            quantidade=Decimal('1'), quantidade_minima=Decimal('2'),
        )

    def test_listagem_requer_autenticacao(self):
        resp = self.client.get('/api/itens/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_admin_pode_listar_itens(self):
        resp = auth_client(self.admin).get('/api/itens/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_endpoint_criticos_retorna_itens_com_estoque_baixo(self):
        resp = auth_client(self.admin).get('/api/itens/criticos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data if isinstance(resp.data, list) else resp.data.get('results', resp.data)
        nomes = [i['nome'] for i in data]
        self.assertIn('Arduino Uno', nomes)
        self.assertIn('Raspberry Pi', nomes)

    def test_usuario_comum_nao_pode_criar_item(self):
        payload = {'nome': 'Novo Item', 'quantidade': '10'}
        resp = auth_client(self.user).post('/api/itens/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Emprestimo — API
# ---------------------------------------------------------------------------

class EmprestimoAPITest(APITestCase):

    def setUp(self):
        from inventario.models import Categoria, Item
        self.admin = create_superuser()
        self.user = create_user()
        cat = Categoria.objects.create(nome='Medição')
        self.item = Item.objects.create(
            nome='Paquímetro', categoria=cat, quantidade=Decimal('5'),
        )

    def test_criar_emprestimo_requer_admin(self):
        payload = {
            'item': self.item.pk,
            'usuario': self.user.pk,
            'quantidade': '1',
            'data_prevista_devolucao': (timezone.now() + timedelta(days=7)).isoformat(),
        }
        resp = auth_client(self.user).post('/api/emprestimos/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_pode_criar_emprestimo(self):
        payload = {
            'item': self.item.pk,
            'usuario': self.user.pk,
            'quantidade': '1',
            'data_prevista_devolucao': (timezone.now() + timedelta(days=7)).isoformat(),
            'responsavel_emprestimo': self.admin.pk,
        }
        resp = auth_client(self.admin).post('/api/emprestimos/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

    def test_devolver_emprestimo_via_action(self):
        from inventario.models import Emprestimo
        emp = Emprestimo.objects.create(
            item=self.item, usuario=self.user, quantidade=Decimal('1'),
            data_prevista_devolucao=timezone.now() + timedelta(days=3),
            responsavel_emprestimo=self.admin,
        )
        resp = auth_client(self.admin).post(f'/api/emprestimos/{emp.pk}/devolver/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        emp.refresh_from_db()
        self.assertIsNotNone(emp.data_devolucao)
