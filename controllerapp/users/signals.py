from django.db.models.signals import m2m_changed, post_migrate
from django.dispatch import receiver

from .models import CustomUser, Role
from .roles import DEFAULT_ROLES


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    """Garante que os cargos padrão existem após migrar."""
    if sender.name != "users":
        return

    for role_data in DEFAULT_ROLES:
        Role.objects.update_or_create(
            code=role_data["code"],
            defaults={
                "name": role_data["name"],
                "description": role_data["description"],
                "is_staff_equivalent": role_data["is_staff_equivalent"],
            },
        )


@receiver(m2m_changed, sender=CustomUser.roles.through)
def sync_staff_flag(sender, instance, action, **kwargs):
    """Mantém o campo is_staff alinhado com cargos que exigem acesso interno."""
    if action in {"post_add", "post_remove", "post_clear"}:
        has_staff_role = instance.roles.filter(is_staff_equivalent=True).exists()
        instance.is_staff = instance.is_superuser or has_staff_role
        instance.save(update_fields=["is_staff"])
