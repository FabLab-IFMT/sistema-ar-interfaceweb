import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Estufa, LeituraEstufa


class ApiTelemetriaTests(TestCase):
    def setUp(self):
        self.estufa = Estufa.objects.create(nome='Estufa Teste')
        self.url = reverse('estufa:api_telemetria')
        self.payload = {
            'modo': 'ARMAZEM',
            'estado': 'ESTAVEL',
            'temperatura_media': 24.5,
            'umidade_media': 40,
            'lampada': False,
            'cooler': False,
            't1': 24.1, 'h1': 41, 't2': 24.9, 'h2': 39,
        }

    def _post(self, payload=None, token=None):
        return self.client.post(
            self.url,
            data=json.dumps(payload or self.payload),
            content_type='application/json',
            headers={'X-Estufa-Token': token or self.estufa.token},
        )

    def test_telemetria_cria_leitura_e_atualiza_estufa(self):
        resposta = self._post()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['modo_desejado'], 'ARMAZEM')
        self.assertEqual(LeituraEstufa.objects.count(), 1)
        self.estufa.refresh_from_db()
        self.assertEqual(self.estufa.temperatura_media, 24.5)
        self.assertTrue(self.estufa.online)

    def test_telemetria_sem_token_retorna_401(self):
        resposta = self.client.post(self.url, data=json.dumps(self.payload),
                                    content_type='application/json')
        self.assertEqual(resposta.status_code, 401)

    def test_telemetria_token_invalido_retorna_403(self):
        resposta = self._post(token='token-errado')
        self.assertEqual(resposta.status_code, 403)

    def test_telemetria_responde_modo_desejado_pendente(self):
        self.estufa.modo_desejado = 'SECAGEM'
        self.estufa.save()
        resposta = self._post()
        self.assertEqual(resposta.json()['modo_desejado'], 'SECAGEM')

    def test_botao_fisico_atualiza_modo_desejado(self):
        payload = dict(self.payload, modo='SECAGEM', origem_botao=True)
        self._post(payload)
        self.estufa.refresh_from_db()
        self.assertEqual(self.estufa.modo_desejado, 'SECAGEM')

    def test_modo_invalido_retorna_400(self):
        resposta = self._post(dict(self.payload, modo='TURBO'))
        self.assertEqual(resposta.status_code, 400)


class DefinirModoTests(TestCase):
    def setUp(self):
        self.estufa = Estufa.objects.create(nome='Estufa Teste')
        User = get_user_model()
        self.user = User.objects.create_user(id='1234567', email='teste@ifmt.edu.br',
                                             password='senha-teste-123')

    def test_exige_login(self):
        resposta = self.client.post(reverse('estufa:definir_modo', args=[self.estufa.id]),
                                    {'modo': 'SECAGEM'})
        self.assertEqual(resposta.status_code, 302)

    def test_define_modo(self):
        self.client.force_login(self.user)
        resposta = self.client.post(reverse('estufa:definir_modo', args=[self.estufa.id]),
                                    {'modo': 'SECAGEM'})
        self.assertEqual(resposta.status_code, 200)
        self.estufa.refresh_from_db()
        self.assertEqual(self.estufa.modo_desejado, 'SECAGEM')
