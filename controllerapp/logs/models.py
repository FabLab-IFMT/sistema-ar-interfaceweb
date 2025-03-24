from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser

class Action(models.Model):
    class SeverityLevel(models.TextChoices):
        INFO = 'info', _('Informação')
        WARNING = 'warning', _('Atenção')
        ERROR = 'error', _('Erro')
        CRITICAL = 'critical', _('Crítico')
        SECURITY = 'security', _('Segurança')
    
    # Tornar todos os campos não-essenciais opcionais
    author = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    url = models.CharField(max_length=255, blank=True, null=True)
    severity = models.CharField(
        max_length=20,
        choices=SeverityLevel.choices,
        default=SeverityLevel.INFO
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.type} - {self.date} {self.time}"
    
    class Meta:
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['severity']),
        ]

class Event(models.Model):
    class EventType(models.TextChoices):
        INTERNAL = 'internal', _('Evento Interno')
        WORKSHOP = 'workshop', _('Workshop')
        VISIT = 'visit', _('Visita Agendada')
        MAINTENANCE = 'maintenance', _('Manutenção')
        OTHER = 'other', _('Outro')
    
    title = models.CharField(_("Título"), max_length=200)
    description = models.TextField(_("Descrição"), blank=True)
    start_time = models.DateTimeField(_("Hora de Início"))
    end_time = models.DateTimeField(_("Hora de Término"))
    event_type = models.CharField(
        _("Tipo de Evento"),
        max_length=20,
        choices=EventType.choices,
        default=EventType.INTERNAL
    )
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="created_events"
    )
    approved = models.BooleanField(_("Aprovado"), default=False)
    participants = models.ManyToManyField(
        CustomUser, 
        related_name="events", 
        blank=True,
        verbose_name=_("Participantes")
    )
    
    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()}) - {self.start_time.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        ordering = ['start_time']
        verbose_name = _("Evento")
        verbose_name_plural = _("Eventos")

class LabSchedule(models.Model):
    DAY_CHOICES = [
        (0, _('Segunda-feira')),
        (1, _('Terça-feira')),
        (2, _('Quarta-feira')),
        (3, _('Quinta-feira')),
        (4, _('Sexta-feira')),
        (5, _('Sábado')),
        (6, _('Domingo')),
    ]
    
    day_of_week = models.IntegerField(_("Dia da Semana"), choices=DAY_CHOICES)
    opening_time = models.TimeField(_("Horário de Abertura"))
    closing_time = models.TimeField(_("Horário de Fechamento"))
    is_closed = models.BooleanField(_("Fechado"), default=False)
    
    class Meta:
        verbose_name = _("Horário de Funcionamento")
        verbose_name_plural = _("Horários de Funcionamento")
        ordering = ['day_of_week']
        
    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_of_week_display()}: Fechado"
        return f"{self.get_day_of_week_display()}: {self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')}"
