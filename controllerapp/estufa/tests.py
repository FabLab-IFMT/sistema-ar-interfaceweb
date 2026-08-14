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


class ApiComandosTests(TestCase):
    def setUp(self):
        self.estufa = Estufa.objects.create(nome='Estufa Teste')
        self.url = reverse('estufa:api_comandos')

    def test_comandos_retorna_estado_desejado_completo(self):
        self.estufa.modo_desejado = 'SECAGEM'
        self.estufa.controle = 'MANUAL'
        self.estufa.lampada_desejada = True
        self.estufa.temp_alvo_sec = 48.0
        self.estufa.save()

        resposta = self.client.get(self.url, headers={'X-Estufa-Token': self.estufa.token})
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        self.assertEqual(dados['modo_desejado'], 'SECAGEM')
        self.assertEqual(dados['controle'], 'MANUAL')
        self.assertTrue(dados['lampada_desejada'])
        self.assertEqual(dados['temp_alvo_sec'], 48.0)

    def test_comandos_atualiza_ultimo_contato(self):
        self.assertIsNone(self.estufa.ultimo_contato)
        self.client.get(self.url, headers={'X-Estufa-Token': self.estufa.token})
        self.estufa.refresh_from_db()
        self.assertIsNotNone(self.estufa.ultimo_contato)
        self.assertTrue(self.estufa.online)

    def test_comandos_token_invalido_retorna_403(self):
        resposta = self.client.get(self.url, headers={'X-Estufa-Token': 'errado'})
        self.assertEqual(resposta.status_code, 403)


class ControleManualTests(TestCase):
    def setUp(self):
        self.estufa = Estufa.objects.create(nome='Estufa Teste')
        User = get_user_model()
        self.user = User.objects.create_user(id='1234567', email='teste@ifmt.edu.br',
                                             password='senha-teste-123')
        self.client.force_login(self.user)

    def test_atuador_ativa_controle_manual(self):
        resposta = self.client.post(
            reverse('estufa:definir_atuador', args=[self.estufa.id]),
            {'atuador': 'lampada', 'acao': 'on'})
        self.assertEqual(resposta.status_code, 200)
        self.estufa.refresh_from_db()
        self.assertEqual(self.estufa.controle, 'MANUAL')
        self.assertTrue(self.estufa.lampada_desejada)

    def test_atuador_cooler_off(self):
        self.estufa.controle = 'MANUAL'
        self.estufa.cooler_desejado = True
        self.estufa.save()
        self.client.post(reverse('estufa:definir_atuador', args=[self.estufa.id]),
                         {'atuador': 'cooler', 'acao': 'off'})
        self.estufa.refresh_from_db()
        self.assertFalse(self.estufa.cooler_desejado)

    def test_atuador_invalido_retorna_400(self):
        resposta = self.client.post(
            reverse('estufa:definir_atuador', args=[self.estufa.id]),
            {'atuador': 'turbina', 'acao': 'on'})
        self.assertEqual(resposta.status_code, 400)

    def test_voltar_para_auto(self):
        self.estufa.controle = 'MANUAL'
        self.estufa.save()
        self.client.post(reverse('estufa:definir_controle', args=[self.estufa.id]),
                         {'controle': 'AUTO'})
        self.estufa.refresh_from_db()
        self.assertEqual(self.estufa.controle, 'AUTO')


class ParametrosTests(TestCase):
    def setUp(self):
        self.estufa = Estufa.objects.create(nome='Estufa Teste')
        User = get_user_model()
        self.user = User.objects.create_user(id='1234567', email='teste@ifmt.edu.br',
                                             password='senha-teste-123')
        self.client.force_login(self.user)
        self.url = reverse('estufa:definir_parametros', args=[self.estufa.id])
        self.validos = {
            'temp_alvo_sec': 47, 'temp_max_sec': 52, 'histerese_sec': 1.5,
            'temp_min_arm': 16, 'temp_max_arm': 28,
        }

    def test_salva_parametros_validos(self):
        resposta = self.client.post(self.url, self.validos)
        self.assertEqual(resposta.status_code, 200)
        self.estufa.refresh_from_db()
        self.assertEqual(self.estufa.temp_alvo_sec, 47)
        self.assertEqual(self.estufa.temp_max_arm, 28)

    def test_rejeita_alvo_maior_que_max(self):
        resposta = self.client.post(self.url, dict(self.validos, temp_alvo_sec=55))
        self.assertEqual(resposta.status_code, 400)

    def test_rejeita_fora_da_faixa(self):
        resposta = self.client.post(self.url, dict(self.validos, temp_max_sec=90))
        self.assertEqual(resposta.status_code, 400)

    def test_rejeita_min_arm_maior_que_max_arm(self):
        resposta = self.client.post(self.url, dict(self.validos, temp_min_arm=30))
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
