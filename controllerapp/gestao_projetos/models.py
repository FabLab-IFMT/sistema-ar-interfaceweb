from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from projetos.models import Projeto

User = get_user_model()

class GrupoProjetos(models.Model):
    """Modelo para agrupar projetos e usuários que podem ter acesso a serviços"""
    nome = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    descricao = models.TextField(help_text="Descrição do grupo de projetos")
    
    # Relacionamentos
    projetos = models.ManyToManyField(Projeto, blank=True, related_name='grupos_gestao')
    membros = models.ManyToManyField(User, blank=True, related_name='grupos_projetos')
    
    # Campos de sistema
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grupos_gestao_criados')
    
    class Meta:
        verbose_name = 'Grupo de Projetos'
        verbose_name_plural = 'Grupos de Projetos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
