from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse

User = get_user_model()


class CategoriaCurso(models.Model):
    nome  = models.CharField(max_length=100)
    slug  = models.SlugField(max_length=100, unique=True)
    icone = models.CharField(max_length=50, default='fa-chalkboard-teacher',
                             help_text="Ícone FontAwesome (ex: fa-print)")
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Categoria de Curso'
        verbose_name_plural = 'Categorias de Cursos'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Curso(models.Model):
    STATUS_CHOICES = [
        ('planejado',    'Planejado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido',    'Concluído'),
        ('cancelado',    'Cancelado'),
    ]

    titulo          = models.CharField(max_length=200)
    slug            = models.SlugField(max_length=200, unique=True)
    descricao_curta = models.CharField(max_length=300,
                                       help_text="Resumo exibido nos cards")
    descricao       = models.TextField(help_text="Conteúdo completo do curso")
    imagem          = models.ImageField(upload_to='cursos/', blank=True, null=True)

    categoria  = models.ForeignKey(CategoriaCurso, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='cursos')
    instrutor  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='cursos_ministrados')

    carga_horaria = models.PositiveIntegerField(null=True, blank=True,
                                                help_text="Em horas")
    data_inicio   = models.DateField(null=True, blank=True)
    data_fim      = models.DateField(null=True, blank=True)
    vagas         = models.PositiveIntegerField(null=True, blank=True,
                                                help_text="Deixe em branco para vagas ilimitadas")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planejado')

    publicado       = models.BooleanField(default=True)
    destaque        = models.BooleanField(default=False)
    mostrar_na_home = models.BooleanField(default=False)

    # Relação com projetos do FabLab (opcional)
    projetos_relacionados = models.ManyToManyField(
        'projetos.Projeto',
        blank=True,
        related_name='cursos_relacionados',
        help_text="Projetos do FabLab desenvolvidos neste curso ou relacionados a ele"
    )

    criado_por    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='cursos_criados')
    criado_em     = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-criado_em']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)
            slug = base
            i = 1
            while Curso.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cursos:detalhe', args=[self.slug])
