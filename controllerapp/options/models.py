from django.db import models
from django.conf import settings
from django.contrib.auth.models import User



# Create your models here.
class Material(models.Model):
    Nome_do_meterial = models.CharField(max_length=100)
    imagem_do_material = models.ImageField(upload_to='materials/')
    descrição_do_material = models.TextField()

    def __str__(self):
        return self.Nome_do_meterial

class Membro(models.Model):
    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    foto = models.ImageField(upload_to='membros/', blank=True)
    bio = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    lattes = models.URLField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    data_entrada = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Membro'
        verbose_name_plural = 'Membros'
    
    def __str__(self):
        return self.nome

class CategoriaServico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=50, help_text="Nome do ícone FontAwesome (ex: fa-print)")
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Categoria de Serviço'
        verbose_name_plural = 'Categorias de Serviços'
    
    def __str__(self):
        return self.nome

class Servico(models.Model):
    categoria = models.ForeignKey(CategoriaServico, on_delete=models.CASCADE, related_name='servicos')
    nome = models.CharField(max_length=100)
    descricao_curta = models.CharField(max_length=200)
    descricao = models.TextField()
    imagem = models.ImageField(upload_to='servicos/', blank=True)
    preco_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Preço base ou mínimo")
    preco_adicional = models.TextField(blank=True, help_text="Explicação sobre custos adicionais ou variáveis")
    tempo_estimado = models.CharField(max_length=100, blank=True, help_text="Ex: '2-3 dias', '1 semana', etc.")
    disponivel = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False, help_text="Serviço em destaque na página inicial")
    ordem = models.PositiveIntegerField(default=0)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
    
    def __str__(self):
        return self.nome

class ProjetoExemplo(models.Model):
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='exemplos')
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    imagem = models.ImageField(upload_to='exemplos_servicos/')
    data = models.DateField()
    
    def __str__(self):
        return self.titulo

class SolicitacaoOrcamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('analise', 'Em Análise'),
        ('respondido', 'Orçamento Enviado'),
        ('aprovado', 'Aprovado pelo Cliente'),
        ('recusado', 'Recusado pelo Cliente'),
        ('concluido', 'Serviço Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, blank=True)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    descricao_projeto = models.TextField(help_text="Descreva seu projeto ou necessidade em detalhes")
    arquivo_referencia = models.FileField(upload_to='orcamentos/', blank=True, null=True, help_text="Arquivo de referência ou modelo")
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    valor_orcado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observacoes_admin = models.TextField(blank=True, help_text="Observações internas (visíveis apenas para staff)")
    
    class Meta:
        verbose_name = 'Solicitação de Orçamento'
        verbose_name_plural = 'Solicitações de Orçamentos'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        return f"Orçamento {self.id} - {self.servico.nome} ({self.nome})"
