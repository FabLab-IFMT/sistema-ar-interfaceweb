from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager

# Create your models here.

class CustomUser(AbstractUser):
    """
    Custom user model that fits IFMT's use case, adding a numerical
    ID that serves as the USERNAME_FIELD.
    """

    username = None
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    email = models.EmailField(_("email address"), blank=False)

    id = models.CharField(_("matricula"), 
        max_length=13 ,
        unique=True, 
        primary_key=True,
        help_text=_(
            "Seu número de matrícula do SUAP ou SIAPE. Apenas números."
        ),
        error_messages={
            "unique": _("Um usuário com este número de matrícula já está cadastrado.")
        }
    )

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = ["first_name", "last_name", "email"]

    objects = CustomUserManager()

    def clean(self):
        from django.core.exceptions import ValidationError
 
        if not self.id.isdigit():
            raise ValidationError("O campo da matrícula pode conter apenas números.")

    def __str__(self):
        return self.id