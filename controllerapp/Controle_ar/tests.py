import shutil
import tempfile
from PIL import Image
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import make_image_file, create_user, create_superuser, auth_client

TEMP_DIR = tempfile.mkdtemp()


# ---------------------------------------------------------------------------
# WebPImageField
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_DIR)
class WebPImageFieldTest(TestCase):
    """Testa a conversão automática para WebP no campo customizado."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        super().tearDownClass()

    def _criar_carousel(self, arquivo, **kwargs):
        from Controle_ar.models import CarouselImage
        c = CarouselImage(image=arquivo, active=True, **kwargs)
        c.save()
        return c

    def test_jpeg_convertido_para_webp(self):
        c = self._criar_carousel(make_image_file('foto.jpg', 'JPEG'))
        self.assertTrue(c.image.name.endswith('.webp'))

    def test_png_convertido_para_webp(self):
        c = self._criar_carousel(make_image_file('foto.png', 'PNG'))
        self.assertTrue(c.image.name.endswith('.webp'))

    def test_arquivo_salvo_e_realmente_webp(self):
        c = self._criar_carousel(make_image_file('foto.jpg', 'JPEG'))
        c.image.open('rb')
        self.assertEqual(Image.open(c.image).format, 'WEBP')

    def test_imagem_rgba_preservada(self):
        c = self._criar_carousel(make_image_file('rgba.png', 'PNG', mode='RGBA'))
        self.assertTrue(c.image.name.endswith('.webp'))
        c.image.open('rb')
        self.assertIn(Image.open(c.image).mode, ('RGBA', 'RGB'))

    def test_nome_base_preservado_na_conversao(self):
        c = self._criar_carousel(make_image_file('banner_principal.jpg', 'JPEG'))
        self.assertIn('banner_principal', c.image.name)

    def test_arquivo_ja_salvo_nao_e_reprocessado(self):
        c = self._criar_carousel(make_image_file('foto.jpg', 'JPEG'))
        nome = c.image.name
        c.caption = 'Legenda alterada'
        c.save()
        self.assertEqual(c.image.name, nome)


# ---------------------------------------------------------------------------
# Carousel — API
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_DIR)
class CarouselAPITest(APITestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        from Controle_ar.models import CarouselImage
        self.admin = create_superuser()
        self.user = create_user()
        CarouselImage.objects.create(active=True, caption='Slide Ativo')
        CarouselImage.objects.create(active=False, caption='Slide Inativo')

    def test_listagem_publica_sem_autenticacao(self):
        resp = self.client.get('/api/carousel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_lista_exibe_apenas_ativos(self):
        resp = self.client.get('/api/carousel/')
        captions = [i['caption'] for i in resp.data.get('results', resp.data)]
        self.assertIn('Slide Ativo', captions)
        self.assertNotIn('Slide Inativo', captions)

    def test_usuario_comum_nao_pode_criar(self):
        resp = auth_client(self.user).post(
            '/api/carousel/', {'image': make_image_file(), 'active': True}, format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cria_e_recebe_url_webp(self):
        resp = auth_client(self.admin).post(
            '/api/carousel/', {'image': make_image_file('banner.jpg'), 'active': True}, format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data['image'].endswith('.webp'))

    def test_sem_auth_nao_pode_criar(self):
        resp = self.client.post(
            '/api/carousel/', {'image': make_image_file(), 'active': True}, format='multipart'
        )
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------------------------------------------------------------------------
# Ar condicionado — model
# ---------------------------------------------------------------------------

class ArCondicionadoModelTest(TestCase):

    def setUp(self):
        from Controle_ar.models import Ar_condicionado
        self.ar = Ar_condicionado.objects.create(
            nome='Sala A', tag='sala-a', estado=False,
            temperatura=22, modo='cold', velocidade=2,
        )

    def test_str_contem_nome(self):
        self.assertIn('Sala A', str(self.ar))

    def test_modo_display_refrigeracao(self):
        self.assertEqual(self.ar.modo_display, 'Refrigeração')

    def test_velocidade_display_media(self):
        self.assertEqual(self.ar.velocidade_display, 'Média')


# ---------------------------------------------------------------------------
# Ar condicionado — API
# ---------------------------------------------------------------------------

class ArCondicionadoAPITest(APITestCase):

    def setUp(self):
        from Controle_ar.models import Ar_condicionado
        self.admin = create_superuser()
        self.user = create_user()
        self.ar = Ar_condicionado.objects.create(
            nome='Lab Principal', tag='lab-01', estado=False, temperatura=24,
        )

    def test_lista_requer_autenticacao(self):
        resp = self.client.get('/api/ar-condicionados/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_toggle_liga_ar_desligado(self):
        auth_client(self.admin).post(f'/api/ar-condicionados/{self.ar.pk}/toggle/')
        self.ar.refresh_from_db()
        self.assertTrue(self.ar.estado)

    def test_toggle_duplo_retorna_estado_original(self):
        c = auth_client(self.admin)
        c.post(f'/api/ar-condicionados/{self.ar.pk}/toggle/')
        c.post(f'/api/ar-condicionados/{self.ar.pk}/toggle/')
        self.ar.refresh_from_db()
        self.assertFalse(self.ar.estado)

    def test_set_temperature_atualiza_valor(self):
        resp = auth_client(self.admin).post(
            f'/api/ar-condicionados/{self.ar.pk}/set_temperature/',
            {'temperature': 18}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.ar.refresh_from_db()
        self.assertEqual(self.ar.temperatura, 18)

    def test_usuario_comum_nao_pode_toggle(self):
        resp = auth_client(self.user).post(f'/api/ar-condicionados/{self.ar.pk}/toggle/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
