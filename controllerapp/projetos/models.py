from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjetoTag(models.Model):
    """Tags para categorizar projetos"""
    nome = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    
    class Meta:
        verbose_name = 'Tag de Projeto'
        verbose_name_plural = 'Tags de Projetos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

class Projeto(models.Model):
    """Modelo para projetos desenvolvidos no FabLab"""
    STATUS_CHOICES = (
        ('concluido', 'Concluído'),
        ('em_andamento', 'Em Andamento'),
        ('planejado', 'Planejado'),
        ('cancelado', 'Cancelado'),
    )
    
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    descricao_curta = models.CharField(max_length=250, help_text="Descrição curta para exibição em cards")
    descricao = models.TextField(help_text="Descrição completa do projeto")
    imagem = models.ImageField(upload_to='projetos/', help_text="Imagem principal do projeto")
    
    # Metadados
    data_inicio = models.DateField()
    data_conclusao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento')
    
    # Relacionamentos
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_responsavel')
    participantes = models.ManyToManyField(User, blank=True, related_name='projetos_participante')
    tags = models.ManyToManyField(ProjetoTag, blank=True, related_name='projetos')
    
    # Links externos
    link_github = models.URLField(blank=True, null=True, help_text="Link para repositório no GitHub")
    link_video = models.URLField(blank=True, null=True, help_text="Link para vídeo do projeto")
    link_documentacao = models.URLField(blank=True, null=True, help_text="Link para documentação")
    
    # Controles de exibição
    mostrar_na_home = models.BooleanField(default=False, help_text="Se marcado, o projeto será exibido na página inicial")
    publicado = models.BooleanField(default=True, help_text="Se marcado, o projeto estará visível no site")
    destaque = models.BooleanField(default=False, help_text="Se marcado, receberá destaque visual")
    
    # Campos de sistema
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('projetos:detalhe', args=[self.slug])

class ProjetoImagem(models.Model):
    """Imagens adicionais para os projetos"""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='imagens_adicionais')
    titulo = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='projetos/imagens/')
    legenda = models.CharField(max_length=200, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Imagem do Projeto'
        verbose_name_plural = 'Imagens dos Projetos'
        ordering = ['ordem']
    
    def __str__(self):
        return self.titulo

