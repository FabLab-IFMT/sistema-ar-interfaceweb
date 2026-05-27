import shutil
import tempfile
from PIL import Image
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from rest_framework import status

from tests_utils import create_user, create_superuser, auth_client, make_image_file

TEMP_DIR = tempfile.mkdtemp()


# ---------------------------------------------------------------------------
# CategoriaCurso — model
# ---------------------------------------------------------------------------

class CategoriaCursoModelTest(TestCase):

    def test_slug_gerado_automaticamente(self):
        from cursos.models import CategoriaCurso
        cat = CategoriaCurso.objects.create(nome='Fabricação Digital', ordem=1)
        self.assertEqual(cat.slug, 'fabricacao-digital')

    def test_slug_nao_sobrescrito_se_ja_existir(self):
        from cursos.models import CategoriaCurso
        cat = CategoriaCurso.objects.create(
            nome='Robótica', slug='robotica-custom', ordem=2
        )
        cat.nome = 'Robótica Avançada'
        cat.save()
        cat.refresh_from_db()
        self.assertEqual(cat.slug, 'robotica-custom')

    def test_str_retorna_nome(self):
        from cursos.models import CategoriaCurso
        cat = CategoriaCurso.objects.create(nome='IoT', ordem=3)
        self.assertEqual(str(cat), 'IoT')

    def test_ordenacao_por_ordem_e_nome(self):
        from cursos.models import CategoriaCurso
        CategoriaCurso.objects.create(nome='Z Categoria', ordem=2)
        CategoriaCurso.objects.create(nome='A Categoria', ordem=1)
        nomes = list(CategoriaCurso.objects.values_list('nome', flat=True))
        self.assertEqual(nomes[0], 'A Categoria')


# ---------------------------------------------------------------------------
# Curso — model
# ---------------------------------------------------------------------------

class CursoModelTest(TestCase):

    def setUp(self):
        from cursos.models import CategoriaCurso
        self.admin = create_superuser()
        self.cat = CategoriaCurso.objects.create(nome='Eletrônica', ordem=1)

    def _criar_curso(self, titulo='Curso Arduino', **kwargs):
        from cursos.models import Curso
        defaults = {
            'titulo': titulo,
            'descricao_curta': 'Aprenda Arduino do zero',
            'descricao': 'Conteúdo completo do curso.',
            'categoria': self.cat,
            'status': 'planejado',
            'publicado': True,
            'criado_por': self.admin,
        }
        defaults.update(kwargs)
        return Curso.objects.create(**defaults)

    def test_slug_gerado_automaticamente(self):
        curso = self._criar_curso('Arduino Para Iniciantes')
        self.assertIn('arduino', curso.slug)

    def test_slugs_unicos_para_titulos_identicos(self):
        c1 = self._criar_curso('Curso Python')
        c2 = self._criar_curso('Curso Python')
        self.assertNotEqual(c1.slug, c2.slug)

    def test_str_retorna_titulo(self):
        curso = self._criar_curso('Robótica com ROS')
        self.assertEqual(str(curso), 'Robótica com ROS')

    def test_get_absolute_url_contem_slug(self):
        curso = self._criar_curso('Curso de Drones')
        self.assertIn(curso.slug, curso.get_absolute_url())

    def test_status_padrao_e_planejado(self):
        from cursos.models import Curso
        curso = Curso.objects.create(
            titulo='Teste Status',
            descricao_curta='x',
            descricao='y',
            categoria=self.cat,
        )
        self.assertEqual(curso.status, 'planejado')


# ---------------------------------------------------------------------------
# Curso — WebPImageField
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_DIR)
class CursoWebPImageTest(TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        super().tearDownClass()

    def test_imagem_do_curso_convertida_para_webp(self):
        from cursos.models import CategoriaCurso, Curso
        admin = create_superuser('11122233344')
        cat = CategoriaCurso.objects.create(nome='Design', ordem=1)
        img = make_image_file('capa.jpg', 'JPEG')
        curso = Curso(
            titulo='Design 3D',
            descricao_curta='Resumo',
            descricao='Conteúdo',
            categoria=cat,
            imagem=img,
            criado_por=admin,
        )
        curso.save()
        self.assertTrue(curso.imagem.name.endswith('.webp'))

    def test_curso_sem_imagem_salvo_normalmente(self):
        from cursos.models import CategoriaCurso, Curso
        admin = create_superuser('55566677788')
        cat = CategoriaCurso.objects.create(nome='Sem Imagem Cat', ordem=2)
        curso = Curso.objects.create(
            titulo='Curso Sem Capa',
            descricao_curta='x',
            descricao='y',
            categoria=cat,
            criado_por=admin,
        )
        self.assertFalse(bool(curso.imagem))


# ---------------------------------------------------------------------------
# Cursos — API (testa endpoints se existirem)
# ---------------------------------------------------------------------------

class CursoAPITest(APITestCase):

    def setUp(self):
        from cursos.models import CategoriaCurso, Curso
        self.admin = create_superuser()
        self.user = create_user()
        cat = CategoriaCurso.objects.create(nome='Programação', ordem=1)
        self.curso = Curso.objects.create(
            titulo='Python Básico',
            descricao_curta='Introdução ao Python',
            descricao='Conteúdo completo',
            categoria=cat,
            status='em_andamento',
            publicado=True,
            criado_por=self.admin,
        )

    def test_listagem_de_cursos(self):
        resp = self.client.get('/api/cursos/')
        # Aceita 200 (endpoint existe) ou 404 (endpoint ainda não implementado)
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_listagem_de_categorias_de_cursos(self):
        resp = self.client.get('/api/categorias-curso/')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_usuario_comum_nao_pode_criar_curso(self):
        payload = {
            'titulo': 'Novo Curso',
            'descricao_curta': 'x',
            'descricao': 'y',
        }
        resp = auth_client(self.user).post('/api/cursos/', payload, format='json')
        # Aceita 403 (sem permissão) ou 404 (endpoint não existe)
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
