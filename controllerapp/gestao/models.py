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

class ConfiguracaoSistema(models.Model):
    """
    Modelo para armazenar configurações do sistema.
    Cada configuração é um par chave-valor com tipo de configuração.
    """
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('booleano', 'Booleano'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('cor', 'Cor'),
        ('data', 'Data'),
        ('hora', 'Hora'),
        ('arquivo', 'Arquivo'),
        ('json', 'JSON'),
        ('senha', 'Senha')
    ]
    
    CATEGORIA_CHOICES = [
        ('geral', 'Geral'),
        ('email', 'Email e Notificações'),
        ('acesso', 'Controle de Acesso'),
        ('visual', 'Aparência'),
        ('integracoes', 'Integrações'),
        ('armazenamento', 'Armazenamento'),
        ('logs', 'Logs e Monitoramento'),
        ('agendamento', 'Agendamento'),
        ('projetos', 'Projetos'),
        ('inventario', 'Inventário'),
        ('avancado', 'Configurações Avançadas'),
    ]

    chave = models.CharField(max_length=100, unique=True, help_text="Nome da configuração (código)")
    nome = models.CharField(max_length=255, help_text="Nome amigável da configuração")
    valor = models.TextField(blank=True, null=True, help_text="Valor da configuração")
    valor_padrao = models.TextField(blank=True, null=True, help_text="Valor padrão da configuração")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='texto', help_text="Tipo de dado da configuração")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='geral', help_text="Categoria da configuração")
    descricao = models.TextField(blank=True, help_text="Descrição da configuração")
    restrito = models.BooleanField(default=False, help_text="Se apenas superusuários podem modificar esta configuração")
    opcoes = models.JSONField(null=True, blank=True, help_text="Opções possíveis para seleção (para configurações com opções limitadas)")
    
    ultima_modificacao = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='configuracoes_modificadas')
    
    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"
        ordering = ['categoria', 'nome']
        
    def __str__(self):
        return f"{self.nome} ({self.chave})"
        
    def obter_valor_tipado(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.valor is None:
            return self.valor_padrao
            
        if self.tipo == 'booleano':
            return self.valor.lower() in ('true', 'sim', 's', 'y', 'yes', '1', 'verdadeiro', 't')
        elif self.tipo == 'numero':
            try:
                return float(self.valor) if '.' in self.valor else int(self.valor)
            except (ValueError, TypeError):
                return 0
        elif self.tipo == 'json':
            try:
                import json
                return json.loads(self.valor)
            except:
                return {}
        else:
            return self.valor

    @staticmethod
    def obter_config(chave, padrao=None):
        """
        Método estático para obter uma configuração pelo seu código.
        Retorna o valor tipado ou o valor padrão se não encontrar.
        """
        try:
            config = ConfiguracaoSistema.objects.get(chave=chave)
            return config.obter_valor_tipado()
        except ConfiguracaoSistema.DoesNotExist:
            return padrao
