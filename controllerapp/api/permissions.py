from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStaffOrReadOnly(BasePermission):
    """Staff pode criar/editar/deletar; outros só leitura."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsSuperUser(BasePermission):
    """Apenas superusuários."""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsGestaoAuthorized(BasePermission):
    """Usuários com acesso à área de gestão (superuser ou acesso_gestao)."""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        try:
            return user.acesso_gestao.tem_acesso
        except Exception:
            return False


class IsOwnerOrStaff(BasePermission):
    """Dono do objeto ou staff. Requer que o objeto tenha campo 'user' ou 'usuario'."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # Tenta diferentes nomes de campo do dono
        owner = getattr(obj, 'user', None) or getattr(obj, 'usuario', None) or getattr(obj, 'created_by', None) or getattr(obj, 'criado_por', None)
        return owner == request.user
