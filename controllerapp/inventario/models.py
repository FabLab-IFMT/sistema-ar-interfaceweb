from django.db import models
from django.conf import settings  # Importamos settings em vez de User diretamente
from django.utils import timezone


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']


class Item(models.Model):
    UNIDADE_CHOICES = [
        ('un', 'Unidade'),
        ('kg', 'Quilograma'),
        ('g', 'Grama'),
        ('l', 'Litro'),
        ('ml', 'Mililitro'),
        ('m', 'Metro'),
        ('cm', 'Centímetro'),
        ('mm', 'Milímetro'),
        ('m²', 'Metro Quadrado'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='itens')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantidade_minima = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidade = models.CharField(max_length=2, choices=UNIDADE_CHOICES, default='un')
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    data_cadastro = models.DateTimeField(default=timezone.now)
    data_atualizacao = models.DateTimeField(auto_now=True)
    imagem = models.ImageField(upload_to='inventario/itens/', blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def valor_total(self):
        if self.valor_unitario:
            return self.quantidade * self.valor_unitario
        return None
    
    @property
    def estoque_baixo(self):
        return self.quantidade <= self.quantidade_minima
    
    @property
    def disponivel_para_emprestimo(self):
        return self.quantidade > 0 and not self.emprestimos.filter(data_devolucao__isnull=True).exists()
    
    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['nome']


class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ('emprestado', 'Emprestado'),
        ('devolvido', 'Devolvido'),
        ('atrasado', 'Atrasado'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='emprestimos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emprestimos')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    data_emprestimo = models.DateTimeField(default=timezone.now)
    data_prevista_devolucao = models.DateTimeField()
    data_devolucao = models.DateTimeField(null=True, blank=True)
    observacao = models.TextField(blank=True, null=True)
    responsavel_emprestimo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                              null=True, related_name='emprestimos_autorizados')
    responsavel_devolucao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                             null=True, blank=True, related_name='devolucoes_recebidas')
    
    def __str__(self):
        return f"{self.item.nome} - {self.usuario.get_full_name()} ({self.data_emprestimo.strftime('%d/%m/%Y')})"
    
    @property
    def status(self):
        if not self.data_devolucao:
            if timezone.now() > self.data_prevista_devolucao:
                return 'atrasado'
            return 'emprestado'
        return 'devolvido'
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES)[self.status]
    
    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-data_emprestimo']
