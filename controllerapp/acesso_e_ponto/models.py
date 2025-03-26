from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser

class WeeklyRequiredHours(models.Model):
    """Define a carga horária semanal mínima para cada usuário."""
    HOURS_CHOICES = (
        (5, '5 horas'),
        (10, '10 horas'),
        (20, '20 horas'),
        (30, '30 horas'),
        (40, '40 horas'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='weekly_hours')
    required_hours = models.PositiveIntegerField(choices=HOURS_CHOICES, default=20, 
                                               verbose_name=_("Horas semanais requeridas"))
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, 
                                   related_name='hours_modifications')
    
    class Meta:
        verbose_name = _("Carga Horária Semanal")
        verbose_name_plural = _("Cargas Horárias Semanais")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.required_hours}h/semana"


class TimeLog(models.Model):
    """Registra os pontos de entrada e saída dos usuários."""
    STATUS_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='time_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    registered_by_card = models.CharField(max_length=20, blank=True, null=True, 
                                        verbose_name=_("Cartão utilizado"))
    
    class Meta:
        verbose_name = _("Registro de Ponto")
        verbose_name_plural = _("Registros de Ponto")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_status_display()} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class Session(models.Model):
    """Representa uma sessão completa (entrada e saída) de um usuário."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Sessão")
        verbose_name_plural = _("Sessões")
        ordering = ['-entry_time']

    def __str__(self):
        if self.is_active:
            return f"{self.user} - Sessão ativa desde {self.entry_time.strftime('%d/%m/%Y %H:%M')}"
        return f"{self.user} - {self.duration} em {self.entry_time.strftime('%d/%m/%Y')}"
    
    def close_session(self):
        """Fecha uma sessão ativa calculando a duração."""
        if self.is_active and not self.exit_time:
            self.exit_time = timezone.now()
            self.duration = self.exit_time - self.entry_time
            self.is_active = False
            self.save()
            return True
        return False
    
    def calculate_duration(self):
        """Calcula a duração de uma sessão mesmo sem fechá-la."""
        if self.exit_time:
            return self.exit_time - self.entry_time
        return timezone.now() - self.entry_time
