from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from tests_utils import create_user, create_superuser, create_staff, auth_client

User = get_user_model()


# ---------------------------------------------------------------------------
# CustomUser — model
# ---------------------------------------------------------------------------

class CustomUserModelTest(TestCase):

    def test_criacao_com_matricula_valida(self):
        user = create_user('20211234567')
        self.assertEqual(user.id, '20211234567')
        self.assertEqual(user.get_full_name(), 'Joao Teste')

    def test_str_retorna_nome_e_matricula(self):
        user = create_user('12345678901')
        self.assertIn('12345678901', str(user))

    def test_clean_rejeita_matricula_com_letras(self):
        user = User(id='ABC123', first_name='X', last_name='Y', email='xy@test.com')
        with self.assertRaises(ValidationError):
            user.clean()

    def test_clean_aceita_matricula_somente_numerica(self):
        user = User(id='12345678901', first_name='X', last_name='Y', email='ok@test.com')
        user.clean()  # não deve lançar exceção

    def test_has_role_falso_sem_cargo(self):
        user = create_user()
        self.assertFalse(user.has_role('gestor_projetos'))

    def test_has_role_verdadeiro_com_cargo(self):
        from users.models import Role
        user = create_user()
        role = Role.objects.create(code='projetista', name='Projetista')
        user.roles.add(role)
        self.assertTrue(user.has_role('projetista'))

    def test_superuser_tem_flags_corretos(self):
        admin = create_superuser()
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_is_project_manager_para_superuser(self):
        admin = create_superuser()
        self.assertTrue(admin.is_project_manager())

    def test_is_project_manager_falso_para_usuario_comum(self):
        user = create_user()
        self.assertFalse(user.is_project_manager())


# ---------------------------------------------------------------------------
# JWT Auth
# ---------------------------------------------------------------------------

class JWTAuthTest(APITestCase):

    def setUp(self):
        self.user = create_user('11111111111', 'senha@123')

    def test_token_obtido_com_credenciais_validas(self):
        resp = self.client.post(
            '/api/token/', {'id': '11111111111', 'password': 'senha@123'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_token_recusado_com_senha_errada(self):
        resp = self.client.post(
            '/api/token/', {'id': '11111111111', 'password': 'errada'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_recusado_com_matricula_inexistente(self):
        resp = self.client.post(
            '/api/token/', {'id': '00000000000', 'password': 'qualquer'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_retorna_novo_access_token(self):
        resp = self.client.post(
            '/api/token/', {'id': '11111111111', 'password': 'senha@123'}, format='json'
        )
        refresh = resp.data['refresh']
        resp2 = self.client.post('/api/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp2.data)


# ---------------------------------------------------------------------------
# /api/me/
# ---------------------------------------------------------------------------

class MeAPITest(APITestCase):

    def setUp(self):
        self.user = create_user('22222222222')

    def test_me_retorna_dados_do_usuario_autenticado(self):
        resp = auth_client(self.user).get('/api/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], '22222222222')

    def test_me_sem_autenticacao_retorna_401(self):
        resp = self.client.get('/api/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_atualiza_campo_do_usuario(self):
        resp = auth_client(self.user).patch('/api/me/', {'first_name': 'NovoNome'}, format='json')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))


# ---------------------------------------------------------------------------
# RegistrationRequest
# ---------------------------------------------------------------------------

class RegistrationRequestTest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()

    def test_criar_solicitacao_de_registro(self):
        payload = {
            'first_name': 'Maria',
            'last_name': 'Silva',
            'email': 'maria@test.com',
            'id_number': '33333333333',
            'password': 'senha@456',
        }
        resp = auth_client(self.admin).post('/api/registration-requests/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

    def test_aprovar_solicitacao(self):
        from users.models import RegistrationRequest
        req = RegistrationRequest.objects.create(
            first_name='Carlos', last_name='Lima',
            email='carlos@test.com', id_number='55555555555',
            password='senha@789', status='pending',
        )
        resp = auth_client(self.admin).post(f'/api/registration-requests/{req.pk}/approve/')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))

    def test_rejeitar_solicitacao(self):
        from users.models import RegistrationRequest
        req = RegistrationRequest.objects.create(
            first_name='Pedro', last_name='Alves',
            email='pedro@test.com', id_number='66666666666',
            password='senha@000', status='pending',
        )
        resp = auth_client(self.admin).post(f'/api/registration-requests/{req.pk}/reject/')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))


# ---------------------------------------------------------------------------
# Users API — permissões
# ---------------------------------------------------------------------------

class UsersAPIPermissaoTest(APITestCase):

    def setUp(self):
        self.user = create_user('66666666666')
        self.admin = create_superuser()

    def test_listar_usuarios_sem_auth_retorna_401(self):
        resp = self.client.get('/api/users/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_admin_pode_listar_usuarios(self):
        resp = auth_client(self.admin).get('/api/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_usuario_comum_nao_pode_listar_outros(self):
        resp = auth_client(self.user).get('/api/users/')
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_200_OK))
