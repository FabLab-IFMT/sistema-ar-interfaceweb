from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date

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

    def _generate_unique_slug(self):
        base_slug = slugify(self.slug or self.titulo)
        slug_candidate = base_slug
        counter = 1
        while Projeto.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
            slug_candidate = f"{base_slug}-{counter}"
            counter += 1
        return slug_candidate
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        elif Projeto.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = self._generate_unique_slug()
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

class ComentarioProjeto(models.Model):
    """Comentários em projetos com suporte a respostas"""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comentarios_projeto')
    texto = models.TextField()
    
    # Suporte para respostas aninhadas
    comentario_pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                      related_name='respostas')
    
    # Campos de status e moderação
    aprovado = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False, help_text="Destacar este comentário")
    
    # Campos de sistema
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Comentário do Projeto'
        verbose_name_plural = 'Comentários dos Projetos'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f'Comentário por {self.autor} em {self.projeto}'
    
    @property
    def is_resposta(self):
        """Verifica se este comentário é uma resposta"""
        return self.comentario_pai is not None

class ProjetoGrupo(models.Model):
    """Grupos de projetos para atribuir tarefas a múltiplos usuários"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    membros = models.ManyToManyField(User, related_name='grupos_projeto')
    projetos = models.ManyToManyField(Projeto, related_name='grupos', blank=True)
    
    # Apenas superusuários podem criar/editar grupos
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grupos_criados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Grupo de Projeto'
        verbose_name_plural = 'Grupos de Projetos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('projetos:grupo_detalhe', args=[self.id])

class TodoTask(models.Model):
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_limite = models.DateField(null=True, blank=True)
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    concluida = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tarefas', null=True, blank=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, null=True, blank=True, related_name='tarefas')
    grupo = models.ForeignKey(ProjetoGrupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='tarefas')
    visivel_para = models.ManyToManyField(User, blank=True, related_name='tarefas_visiveis')
    
    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['-prioridade', 'data_limite', 'titulo']
    
    def __str__(self):
        return self.titulo
    
    @property
    def days_remaining(self):
        if not self.data_limite:
            return None
        
        hoje = date.today()
        return (self.data_limite - hoje).days
    
    @property
    def esta_atrasada(self):
        """Verifica se a tarefa está atrasada"""
        if self.data_limite and not self.concluida:
            return self.data_limite < timezone.now().date()
        return False
    
    @property
    def dias_restantes(self):
        """Calcula os dias restantes até a data limite"""
        if self.data_limite:
            delta = self.data_limite - timezone.now().date()
            return delta.days
        return None


class ProjetoMarco(models.Model):
    """Marco do roadmap do projeto"""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='marcos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data = models.DateField()
    progresso = models.PositiveSmallIntegerField(default=0)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marcos_responsavel')
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marcos_criados')
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['data', 'ordem', 'id']
        verbose_name = 'Marco do Projeto'
        verbose_name_plural = 'Marcos do Projeto'

    def __str__(self):
        return f"{self.titulo} ({self.projeto})"

