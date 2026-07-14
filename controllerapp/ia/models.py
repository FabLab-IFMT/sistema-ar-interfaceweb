from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class InsightIA(models.Model):
    """Insight operacional gerado pela IA a partir dos dados do SGL."""

    class Foco(models.TextChoices):
        GERAL = 'geral', _('Visão Geral')
        AGENDA = 'agenda', _('Agenda e Visitas')
        ESTOQUE = 'estoque', _('Inventário e Estoque')
        PROJETOS = 'projetos', _('Projetos')
        MANUTENCAO = 'manutencao', _('Manutenção e Fluxo')

    foco = models.CharField(
        _('Foco da análise'), max_length=20,
        choices=Foco.choices, default=Foco.GERAL,
    )
    titulo = models.CharField(_('Título'), max_length=200)
    conteudo = models.TextField(_('Conteúdo do insight'))
    dados_contexto = models.JSONField(
        _('Dados enviados à IA'), default=dict, blank=True,
        help_text='Snapshot dos dados operacionais usados na geração.',
    )
    modelo_usado = models.CharField(_('Modelo de IA'), max_length=50, blank=True)
    tokens_usados = models.PositiveIntegerField(_('Tokens consumidos'), default=0)
    gerado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='insights_gerados',
        verbose_name=_('Gerado por'),
    )
    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Insight de IA')
        verbose_name_plural = _('Insights de IA')
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.get_foco_display()} — {self.criado_em.strftime('%d/%m/%Y %H:%M')}"
