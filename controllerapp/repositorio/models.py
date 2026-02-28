from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings
from projetos.models import Projeto
import os
from pathlib import Path

class ResourceCategory(models.Model):
    """Categoria para organizar recursos"""
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField('Descrição', blank=True)
    icon = models.CharField('Ícone', max_length=50, help_text='Nome do ícone FontAwesome (ex: fa-file-pdf)', blank=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    
    class Meta:
        verbose_name = 'Categoria de Recurso'
        verbose_name_plural = 'Categorias de Recursos'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

def resource_file_path(instance, filename):
    """Define o caminho onde o arquivo será salvo"""
    # Obter a extensão do arquivo
    ext = filename.split('.')[-1]
    
    # Se o ResourceFile tem relação com Resource, use o slug do recurso
    if hasattr(instance, 'resource') and instance.resource:
        resource_slug = instance.resource.slug
        project_slug = instance.resource.project.slug
    else:  # Caso seja o arquivo principal do Resource
        resource_slug = instance.slug
        project_slug = instance.project.slug
    
    # Preservar o nome original do arquivo se não houver título definido
    if hasattr(instance, 'title') and instance.title and instance.title != filename:
        filename_base = slugify(instance.title)
        filename = f"{filename_base}.{ext}"
    else:
        # Limpar o nome do arquivo para evitar caracteres problemáticos
        filename = filename.replace(' ', '_').lower()
    
    # Retornar o caminho completo
    return os.path.join('recursos', project_slug, resource_slug, filename)

class Resource(models.Model):
    """Modelo base para todos os recursos"""
    RESOURCE_TYPES = (
        ('document', 'Documento'),
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('code', 'Código'),
        ('text', 'Texto'),
        ('link', 'Link'),
        ('other', 'Outros'),
    )
    
    VISIBILITY_CHOICES = (
        ('public', 'Público'),
        ('members', 'Apenas membros'),
        ('team', 'Apenas equipe interna'),
    )
    
    title = models.CharField('Título', max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField('Descrição', blank=True)
    resource_type = models.CharField('Tipo', max_length=20, choices=RESOURCE_TYPES)
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    project = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='resources')
    visibility = models.CharField('Visibilidade', max_length=20, choices=VISIBILITY_CHOICES, default='members')
    
    # Campo para conteúdo de texto
    text_content = models.TextField('Conteúdo de texto', blank=True)
    
    # Campo para links externos
    external_url = models.URLField('URL externa', blank=True, null=True)
    
    # Metadados
    featured = models.BooleanField('Destacado', default=False, help_text='Se marcado, este recurso será destacado na página do projeto')
    tags = models.CharField('Tags', max_length=200, blank=True, help_text='Tags separadas por vírgula')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_resources')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Garantir que o slug seja único
            while Resource.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('repositorio:resource_detail', args=[self.slug])
    
    @property
    def main_file(self):
        """Retorna o arquivo principal (primeiro arquivo)"""
        files = self.resource_files.all()
        return files.first() if files.exists() else None
    
    def can_view(self, user):
        """Verifica se o usuário tem permissão para visualizar este recurso"""
        # Recursos públicos podem ser vistos por todos
        if self.visibility == 'public':
            return True
            
        # Se não estiver logado, só pode ver recursos públicos
        if not user.is_authenticated:
            return False
            
        # Superusuários podem ver tudo
        if user.is_superuser:
            return True

        # Pesquisadores podem ver recursos públicos e de membros para análise
        if hasattr(user, "has_role") and user.has_role("pesquisador"):
            if self.visibility in {'public', 'members'}:
                return True
            
        # Responsável pelo projeto pode ver tudo do projeto
        if self.project.responsavel == user:
            return True
            
        # Membros do projeto podem ver recursos marcados como 'members'
        if self.visibility == 'members' and user in self.project.participantes.all():
            return True
            
        # Membros da equipe podem ver recursos marcados como 'team'
        if self.visibility == 'team' and user.is_staff:
            return True
            
        # Em todos os outros casos, não tem permissão
        return False
        
    def can_edit(self, user):
        """Verifica se o usuário tem permissão para editar este recurso"""
        # Só usuários logados podem editar
        if not user.is_authenticated:
            return False
            
        # Superusuários podem editar tudo
        if user.is_superuser:
            return True
            
        # Quem criou pode editar
        if self.created_by == user:
            return True
            
        # Responsável pelo projeto pode editar
        if self.project.responsavel == user:
            return True
            
        # Em todos os outros casos, não tem permissão
        return False

class ResourceFile(models.Model):
    """Arquivos associados a um recurso (permitindo múltiplos arquivos)"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='resource_files')
    title = models.CharField('Título', max_length=200, blank=True, help_text='Se em branco, será usado o nome do arquivo')
    file = models.FileField('Arquivo', upload_to=resource_file_path)
    file_size = models.PositiveIntegerField('Tamanho do arquivo (bytes)', blank=True, null=True)
    file_type = models.CharField('Tipo de arquivo', max_length=100, blank=True)
    upload_date = models.DateTimeField('Data de upload', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Arquivo de Recurso'
        verbose_name_plural = 'Arquivos de Recursos'
        ordering = ['upload_date']
    
    def __str__(self):
        return self.title or os.path.basename(self.file.name)
        
    def save(self, *args, **kwargs):
        # Se não houver título, usar o nome do arquivo
        if not self.title and self.file:
            self.title = os.path.basename(self.file.name)
            
        # Atualizar informações do arquivo
        if self.file and not self.file_size:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1]
            
        super().save(*args, **kwargs)
        
    @property
    def filename(self):
        """Nome do arquivo sem o caminho"""
        return os.path.basename(self.file.name) if self.file else None
    
    @property
    def file_extension(self):
        """Extensão do arquivo"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None
        
    @property
    def is_image(self):
        if self.file_extension:
            return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return False
    
    @property
    def is_document(self):
        if self.file_extension:
            return self.file_extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        return False
    
    @property
    def is_code(self):
        if self.file_extension:
            return self.file_extension in ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.php']
        return False
        
    @property
    def is_audio(self):
        if self.file_extension:
            return self.file_extension in ['.mp3', '.wav', '.ogg', '.m4a']
        return False
        
    @property
    def is_video(self):
        if self.file_extension:
            return self.file_extension in ['.mp4', '.webm', '.ogg', '.mov']
        return False

class ResourceComment(models.Model):
    """Comentários em recursos"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField('Comentário')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comentário de {self.user} em {self.resource}"
