import secrets

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def gerar_token():
    return secrets.token_urlsafe(32)


class Estufa(models.Model):
    MODO_SECAGEM = 'SECAGEM'
    MODO_ARMAZEM = 'ARMAZEM'
    MODO_CHOICES = [
        (MODO_SECAGEM, 'Secagem'),
        (MODO_ARMAZEM, 'Armazenamento'),
    ]

    ESTADO_CHOICES = [
        ('AQUECENDO', 'Aquecendo'),
        ('MANTENDO', 'Mantendo'),
        ('RESFRIANDO', 'Resfriando'),
        ('ESTAVEL', 'Estável'),
        ('ERRO', 'Erro nos sensores'),
    ]

    nome = models.CharField(max_length=50, default='Estufa de Filamento')
    token = models.CharField(
        max_length=64, unique=True, default=gerar_token,
        help_text='Token de autenticação do dispositivo (enviado no header X-Estufa-Token)'
    )

    CONTROLE_AUTO = 'AUTO'
    CONTROLE_MANUAL = 'MANUAL'
    CONTROLE_CHOICES = [
        (CONTROLE_AUTO, 'Automático (termostato)'),
        (CONTROLE_MANUAL, 'Manual'),
    ]

    # Modo que o servidor deseja que a estufa opere (comando pendente)
    modo_desejado = models.CharField(max_length=10, choices=MODO_CHOICES, default=MODO_ARMAZEM)

    # Controle manual dos atuadores (quando controle=MANUAL o termostato é ignorado,
    # exceto pela trava de segurança de 55°C gravada no firmware)
    controle = models.CharField(max_length=10, choices=CONTROLE_CHOICES, default=CONTROLE_AUTO)
    lampada_desejada = models.BooleanField(default=False)
    cooler_desejado = models.BooleanField(default=False)

    # Parâmetros do termostato, configuráveis pela interface web
    temp_alvo_sec = models.FloatField(default=45.0, help_text='Temperatura alvo no modo secagem (°C)')
    temp_max_sec = models.FloatField(default=50.0, help_text='Temperatura máxima no modo secagem (°C)')
    histerese_sec = models.FloatField(default=1.0, help_text='Histerese do modo secagem (°C)')
    temp_max_arm = models.FloatField(default=30.0, help_text='Temperatura máxima no armazenamento (°C)')
    temp_min_arm = models.FloatField(default=15.0, help_text='Temperatura mínima no armazenamento (°C)')

    # Último estado reportado pelo dispositivo
    modo_atual = models.CharField(max_length=10, choices=MODO_CHOICES, default=MODO_ARMAZEM)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='ESTAVEL')
    temperatura_media = models.FloatField(null=True, blank=True)
    umidade_media = models.FloatField(null=True, blank=True)
    lampada_ligada = models.BooleanField(default=False)
    cooler_ligado = models.BooleanField(default=False)
    ultimo_contato = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Estufa')
        verbose_name_plural = _('Estufas')

    def __str__(self):
        return self.nome

    @property
    def online(self):
        """Considera online se reportou nos últimos 2 minutos."""
        if not self.ultimo_contato:
            return False
        return (timezone.now() - self.ultimo_contato).total_seconds() < 120


class LeituraEstufa(models.Model):
    estufa = models.ForeignKey(Estufa, on_delete=models.CASCADE, related_name='leituras')
    data_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    modo = models.CharField(max_length=10, choices=Estufa.MODO_CHOICES)
    estado = models.CharField(max_length=12, choices=Estufa.ESTADO_CHOICES)
    temperatura_media = models.FloatField(null=True, blank=True)
    umidade_media = models.FloatField(null=True, blank=True)
    lampada_ligada = models.BooleanField(default=False)
    cooler_ligado = models.BooleanField(default=False)

    # Leituras individuais dos 5 sensores DHT22 (null = sensor com falha)
    t1 = models.FloatField(null=True, blank=True)
    h1 = models.FloatField(null=True, blank=True)
    t2 = models.FloatField(null=True, blank=True)
    h2 = models.FloatField(null=True, blank=True)
    t3 = models.FloatField(null=True, blank=True)
    h3 = models.FloatField(null=True, blank=True)
    t4 = models.FloatField(null=True, blank=True)
    h4 = models.FloatField(null=True, blank=True)
    t5 = models.FloatField(null=True, blank=True)
    h5 = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = _('Leitura da Estufa')
        verbose_name_plural = _('Leituras da Estufa')
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.estufa.nome} - {self.data_hora:%d/%m/%Y %H:%M} ({self.temperatura_media}°C)'


class LogOperacaoEstufa(models.Model):
    estufa = models.ForeignKey(Estufa, on_delete=models.CASCADE, related_name='logs')
    operacao = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Log de Operação da Estufa')
        verbose_name_plural = _('Logs de Operação da Estufa')
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.estufa.nome} - {self.operacao} por {self.usuario}'
