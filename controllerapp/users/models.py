from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .managers import CustomUserManager


class Role(models.Model):
    """Cargo atribuído ao usuário, usado para controlar acesso por perfis."""

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_staff_equivalent = models.BooleanField(
        default=False,
        help_text="Se marcado, o usuário recebe permissões de staff ao ter este cargo.",
    )

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ["name"]

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    username = None
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    email = models.EmailField(_("email address"), blank=False, unique=True, 
                              error_messages={"unique": _("Um usuário com este email já está cadastrado.")})

    profile_image = models.ImageField(upload_to='users/profile/', null=True, blank=True)
    email_verified = models.BooleanField(default=True, help_text="Indica se o email foi confirmado")

    id = models.CharField(_("matricula"), 
        max_length=13,
        unique=True, 
        primary_key=True,
        help_text=_(
            "Seu número de matrícula do SUAP ou SIAPE. Apenas números."
        ),
        error_messages={
            "unique": _("Um usuário com este número de matrícula já está cadastrado.")
        }
    )

    roles = models.ManyToManyField(Role, related_name="users", blank=True)

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = ["first_name", "last_name", "email"]

    objects = CustomUserManager()

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.id.isdigit():
            raise ValidationError("O campo da matrícula pode conter apenas números.")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id})"

    def has_role(self, code: str) -> bool:
        """Retorna True se o usuário possui o cargo informado."""
        return self.roles.filter(code=code).exists()

    def role_codes(self):
        return set(self.roles.values_list("code", flat=True))

    def is_project_manager(self):
        return self.is_superuser or self.is_staff or self.has_role("gestor_projetos")

    def is_projectist(self):
        return self.has_role("projetista")


class Card(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='card')
    card_number = models.CharField(_("Número do Cartão"), max_length=20, unique=True)

    def __str__(self):
        return f'Cartão {self.card_number} - {self.user.first_name} {self.user.last_name}'


class RegistrationRequest(models.Model):
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    email = models.EmailField(_("email address"))
    id_number = models.CharField(_("matricula"), max_length=13)
    password = models.CharField(_("password"), max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number}) - {self.get_status_display()}"


class ProjectistRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendente"),
        ("approved", "Aprovado"),
        ("rejected", "Rejeitado"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="projetista_requests")
    motivation = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="projetista_decisions")

    class Meta:
        verbose_name = "Solicitação de Projetista"
        verbose_name_plural = "Solicitações de Projetista"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.get_status_display()}"
