from datetime import time
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client


# ---------------------------------------------------------------------------
# Action — model
# ---------------------------------------------------------------------------

class ActionModelTest(TestCase):

    def test_criacao_de_log_de_acao(self):
        from logs.models import Action
        import datetime
        log = Action.objects.create(
            type='LOGIN',
            description='Usuário fez login',
            date=datetime.date.today(),
            time=datetime.time(10, 0),
            severity='info',
        )
        self.assertIn('LOGIN', str(log))

    def test_severity_padrao_e_info(self):
        from logs.models import Action
        import datetime
        log = Action.objects.create(
            type='TEST',
            description='Teste de severidade',
            date=datetime.date.today(),
            time=datetime.time(12, 0),
        )
        self.assertEqual(log.severity, 'info')


# ---------------------------------------------------------------------------
# Event — model
# ---------------------------------------------------------------------------

class EventModelTest(TestCase):

    def setUp(self):
        self.user = create_user()

    def test_criacao_de_evento(self):
        from logs.models import Event
        inicio = timezone.now() + timezone.timedelta(days=1)
        fim = inicio + timezone.timedelta(hours=2)
        ev = Event.objects.create(
            title='Workshop Arduino',
            description='Introdução ao Arduino',
            start_time=inicio,
            end_time=fim,
            event_type='workshop',
            created_by=self.user,
        )
        self.assertFalse(ev.approved)
        self.assertIn('Workshop Arduino', str(ev))

    def test_evento_nao_aprovado_por_padrao(self):
        from logs.models import Event
        ev = Event.objects.create(
            title='Evento',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            created_by=self.user,
        )
        self.assertFalse(ev.approved)


# ---------------------------------------------------------------------------
# LabSchedule — model
# ---------------------------------------------------------------------------

class LabScheduleModelTest(TestCase):

    def test_str_horario_aberto(self):
        from logs.models import LabSchedule
        s = LabSchedule.objects.create(
            day_of_week=0,
            opening_time=time(8, 0),
            closing_time=time(17, 0),
            is_closed=False,
        )
        self.assertIn('Segunda-feira', str(s))
        self.assertIn('08:00', str(s))

    def test_str_horario_fechado(self):
        from logs.models import LabSchedule
        s = LabSchedule.objects.create(
            day_of_week=6,
            opening_time=time(8, 0),
            closing_time=time(12, 0),
            is_closed=True,
        )
        self.assertIn('Fechado', str(s))


# ---------------------------------------------------------------------------
# Event — API
# ---------------------------------------------------------------------------

class EventAPITest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()
        self.user = create_user()
        self.inicio = timezone.now() + timezone.timedelta(days=1)
        self.fim = self.inicio + timezone.timedelta(hours=2)

    def test_criar_evento_autenticado(self):
        payload = {
            'title': 'Visita Escola',
            'description': 'Visita de alunos do ensino médio',
            'start_time': self.inicio.isoformat(),
            'end_time': self.fim.isoformat(),
            'event_type': 'visit',
        }
        resp = auth_client(self.user).post('/api/eventos/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

    def test_criar_evento_sem_autenticacao_negado(self):
        payload = {
            'title': 'Evento Anônimo',
            'start_time': self.inicio.isoformat(),
            'end_time': self.fim.isoformat(),
        }
        resp = self.client.post('/api/eventos/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_aprovar_evento_requer_admin(self):
        from logs.models import Event
        ev = Event.objects.create(
            title='Evento Para Aprovar',
            start_time=self.inicio,
            end_time=self.fim,
            created_by=self.user,
        )
        resp = auth_client(self.admin).post(f'/api/eventos/{ev.pk}/approve/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ev.refresh_from_db()
        self.assertTrue(ev.approved)

    def test_usuario_comum_nao_pode_aprovar_evento(self):
        from logs.models import Event
        ev = Event.objects.create(
            title='Evento Pendente',
            start_time=self.inicio,
            end_time=self.fim,
            created_by=self.user,
        )
        resp = auth_client(self.user).post(f'/api/eventos/{ev.pk}/approve/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_endpoint_eventos_pendentes_requer_admin(self):
        resp = auth_client(self.admin).get('/api/eventos/pending/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# LabSchedule — API
# ---------------------------------------------------------------------------

class LabScheduleAPITest(APITestCase):

    def setUp(self):
        self.admin = create_superuser()

    def test_listar_horarios_e_publico(self):
        resp = self.client.get('/api/horarios/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_horario_requer_staff(self):
        payload = {
            'day_of_week': 0,
            'opening_time': '08:00:00',
            'closing_time': '17:00:00',
            'is_closed': False,
        }
        resp = auth_client(self.admin).post('/api/horarios/', payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))
