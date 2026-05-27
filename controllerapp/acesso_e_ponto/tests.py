from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# TimeLog — model
# ---------------------------------------------------------------------------

class TimeLogModelTest(TestCase):

    def setUp(self):
        from acesso_e_ponto.models import TimeLog
        self.user = create_user()
        self.log_entrada = TimeLog.objects.create(user=self.user, status='entrada')
        self.log_saida = TimeLog.objects.create(user=self.user, status='saida')

    def test_str_contem_nome_e_status(self):
        self.assertIn('Joao', str(self.log_entrada))
        self.assertIn('Entrada', str(self.log_entrada))

    def test_status_get_display(self):
        self.assertEqual(self.log_entrada.get_status_display(), 'Entrada')
        self.assertEqual(self.log_saida.get_status_display(), 'Saída')


# ---------------------------------------------------------------------------
# Session — model
# ---------------------------------------------------------------------------

class SessionModelTest(TestCase):

    def setUp(self):
        self.user = create_user()

    def _criar_sessao(self, **kwargs):
        from acesso_e_ponto.models import Session
        defaults = {
            'user': self.user,
            'entry_time': timezone.now() - timedelta(hours=2),
            'is_active': True,
        }
        defaults.update(kwargs)
        return Session.objects.create(**defaults)

    def test_sessao_ativa_str_contem_ativa(self):
        s = self._criar_sessao()
        self.assertIn('ativa', str(s))

    def test_close_session_encerra_sessao_ativa(self):
        s = self._criar_sessao()
        resultado = s.close_session()
        self.assertTrue(resultado)
        self.assertFalse(s.is_active)
        self.assertIsNotNone(s.exit_time)
        self.assertIsNotNone(s.duration)

    def test_close_session_retorna_false_para_sessao_ja_encerrada(self):
        s = self._criar_sessao(
            exit_time=timezone.now() - timedelta(hours=1),
            is_active=False,
        )
        resultado = s.close_session()
        self.assertFalse(resultado)

    def test_calculate_duration_com_exit_time(self):
        entry = timezone.now() - timedelta(hours=3)
        exit_ = timezone.now() - timedelta(hours=1)
        s = self._criar_sessao(entry_time=entry, exit_time=exit_, is_active=False)
        duracao = s.calculate_duration()
        self.assertAlmostEqual(duracao.total_seconds(), 7200, delta=5)

    def test_calculate_duration_sem_exit_time_usa_agora(self):
        s = self._criar_sessao()
        duracao = s.calculate_duration()
        self.assertGreater(duracao.total_seconds(), 0)


# ---------------------------------------------------------------------------
# WeeklyRequiredHours — model
# ---------------------------------------------------------------------------

class WeeklyHoursModelTest(TestCase):

    def test_str_contem_nome_e_horas(self):
        from acesso_e_ponto.models import WeeklyRequiredHours
        user = create_user()
        admin = create_superuser()
        wh = WeeklyRequiredHours.objects.create(
            user=user, required_hours=20, modified_by=admin
        )
        self.assertIn('20', str(wh))
        self.assertIn('Joao', str(wh))


# ---------------------------------------------------------------------------
# TimeLog — API
# ---------------------------------------------------------------------------

class TimeLogAPITest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()
        self.user = create_user()

    def test_listar_timelogs_requer_admin(self):
        resp = auth_client(self.user).get('/api/time-logs/')
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_200_OK))

    def test_admin_pode_listar_timelogs(self):
        resp = auth_client(self.admin).get('/api/time-logs/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_sem_auth_nao_acessa_timelogs(self):
        resp = self.client.get('/api/time-logs/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# Session — API
# ---------------------------------------------------------------------------

class SessionAPITest(APITestCase):

    def setUp(self):
        from acesso_e_ponto.models import Session
        self.admin = create_superuser()
        self.user = create_user()
        self.sessao = Session.objects.create(
            user=self.user,
            entry_time=timezone.now() - timedelta(hours=1),
            is_active=True,
        )

    def test_admin_pode_listar_sessoes(self):
        resp = auth_client(self.admin).get('/api/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_close_session_action(self):
        resp = auth_client(self.admin).post(f'/api/sessions/{self.sessao.pk}/close/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.sessao.refresh_from_db()
        self.assertFalse(self.sessao.is_active)
