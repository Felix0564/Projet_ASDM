from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "agent")

class IsDemandeur(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "demandeur")

class IsOwnerOrReadOnly(BasePermission):
    """
    Pour DossierDemande : le demandeur voit/édite uniquement ses dossiers
    Les agents/admins ont tous les droits.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return (
                obj.utilisateur_id == request.user.id
                or request.user.role in ("agent", "admin")
            )
        return (
            obj.utilisateur_id == request.user.id
            or request.user.role in ("agent", "admin")
        )
