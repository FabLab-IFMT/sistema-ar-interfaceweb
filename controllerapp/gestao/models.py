from django.db import models
from django.conf import settings

class AcessoGestao(models.Model):
    """
    Modelo para controlar quais usuários têm acesso à área de gestão.
    Apenas superusuários podem conceder este acesso.
    """
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acesso_gestao')
    tem_acesso = models.BooleanField(default=False)
    concedido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='permissoes_concedidas')
    data_concessao = models.DateTimeField(auto_now_add=True)
    ultima_modificacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Acesso à Gestão"
        verbose_name_plural = "Acessos à Gestão"
    
    def __str__(self):
        status = "Ativo" if self.tem_acesso else "Inativo"
        return f"{self.usuario.username} - Acesso à Gestão: {status}"

class Configuracao(models.Model):
    """
    Modelo simplificado para armazenar configurações do sistema
    """
    CATEGORIAS = (
        ('geral', 'Configurações Gerais'),
        ('email', 'Email e Notificações'),
        ('laboratorio', 'Configurações do Laboratório'),
        ('sistema', 'Sistema'),
        ('acesso', 'Controle de Acesso')
    )
    
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.CharField(max_length=255)
    valor = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='geral')
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"
        ordering = ['categoria', 'nome']
    
    def __str__(self):
        return f"{self.nome} - {self.get_categoria_display()}"
