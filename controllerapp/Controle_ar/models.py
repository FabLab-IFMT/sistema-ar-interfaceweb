from django.db import models
from django.utils.translation import gettext_lazy as _

class CarouselImage(models.Model):
    image = models.ImageField(upload_to='carousel/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True, help_text="Marque para exibir essa imagem no carrossel.")
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Título da imagem.")
    description = models.TextField(blank=True, null=True, help_text="Descrição exibida junto da imagem.")
    link = models.CharField(max_length=255, blank=True, null=True, help_text="Link para tornar a imagem clicável.")

    def __str__(self):
        return self.caption or f"Imagem {self.pk}"

class Ar_condicionado(models.Model):
    nome = models.CharField(max_length=50)
    tag = models.CharField(max_length=50, unique=True)
    estado = models.BooleanField(default=False)
    temperatura = models.IntegerField(default=20)
    modo = models.CharField(max_length=20, default="cold")
    velocidade = models.IntegerField(default=1)  # 1-3 para baixa, média, alta
    swing = models.BooleanField(default=False)
    ultima_alteracao = models.DateTimeField(auto_now=True)
    
    # Novos campos para registrar o status do equipamento
    online = models.BooleanField(default=True)
    ultimo_ping = models.DateTimeField(null=True, blank=True)
    consumo_atual = models.FloatField(default=0.0, help_text="Consumo atual em kW/h")
    temperatura_ambiente = models.FloatField(null=True, blank=True, help_text="Temperatura ambiente em °C")
    
    # Campo para armazenar o IP do ESP32 (opcional)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP do ESP32 (preenchido automaticamente)")
    
    class Meta:
        verbose_name = _("Ar Condicionado")
        verbose_name_plural = _("Ar Condicionados")
    
    def __str__(self):
        status = "Ligado" if self.estado else "Desligado"
        return f"{self.nome} - {status} ({self.temperatura}°C)"
    
    @property
    def modo_display(self):
        modos = {
            "cold": "Refrigeração",
            "heat": "Aquecimento",
            "fan": "Ventilação",
            "dry": "Desumidificação",
            "auto": "Automático"
        }
        return modos.get(self.modo, "Desconhecido")
    
    @property
    def velocidade_display(self):
        velocidades = {
            1: "Baixa",
            2: "Média", 
            3: "Alta",
            4: "Automática"
        }
        return velocidades.get(self.velocidade, "Desconhecida")

class Comando_ar(models.Model):
    ar_condicionado = models.ForeignKey(Ar_condicionado, on_delete=models.CASCADE)
    comando = models.CharField(max_length=100)
    executado = models.BooleanField(default=False)
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Comando de Ar")
        verbose_name_plural = _("Comandos de Ar")
    
    def __str__(self):
        status = "Executado" if self.executado else "Pendente"
        return f"{self.ar_condicionado.nome} - {self.comando} - {status}"

class LogOperacao(models.Model):
    ar_condicionado = models.ForeignKey(Ar_condicionado, on_delete=models.CASCADE)
    operacao = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100)
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Log de Operação")
        verbose_name_plural = _("Logs de Operação")
    
    def __str__(self):
        return f"{self.ar_condicionado.nome} - {self.operacao} por {self.usuario}"
