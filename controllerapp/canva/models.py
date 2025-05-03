from django.db import models
from django.contrib.auth import get_user_model
from projetos.models import Projeto

User = get_user_model()

class KanbanColumn(models.Model):
    """Representa uma coluna no quadro Kanban (ex: A fazer, Em progresso, Concluído)"""
    nome = models.CharField(max_length=100)
    ordem = models.PositiveIntegerField(default=0)
    cor = models.CharField(max_length=20, default='#f8f9fa')  # Cor de fundo da coluna
    
    class Meta:
        ordering = ['ordem']
        verbose_name = 'Coluna do Kanban'
        verbose_name_plural = 'Colunas do Kanban'
    
    def __str__(self):
        return self.nome

class KanbanCard(models.Model):
    """Representa um cartão/tarefa no quadro Kanban"""
    PRIORITY_CHOICES = (
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    coluna = models.ForeignKey(KanbanColumn, on_delete=models.CASCADE, related_name='cards')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='kanban_cards', null=True, blank=True)
    
    # Membros que podem ver/trabalhar no card
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards_responsavel')
    membros = models.ManyToManyField(User, blank=True, related_name='cards_membro')
    
    # Metadados
    prioridade = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='media')
    data_inicio = models.DateField(null=True, blank=True)
    prazo = models.DateField(null=True, blank=True)
    data_conclusao = models.DateField(null=True, blank=True)
    visivel = models.BooleanField(default=True, help_text="Se marcado, o card será visível no quadro")
    
    # Campos adicionais para monitoramento
    progresso = models.PositiveSmallIntegerField(default=0, help_text="Progresso em percentual (0-100)")
    tempo_trabalhado = models.PositiveIntegerField(default=0, help_text="Tempo trabalhado em segundos")
    notas = models.TextField(blank=True, help_text="Anotações rápidas sobre a tarefa")
    
    # Posicionamento no quadro
    ordem = models.PositiveIntegerField(default=0)
    
    # Campos de sistema
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cards_criados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['coluna', 'ordem']
        verbose_name = 'Card do Kanban'
        verbose_name_plural = 'Cards do Kanban'
    
    def __str__(self):
        return self.titulo
