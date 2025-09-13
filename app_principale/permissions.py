from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedCustom(BasePermission):
    """
    Permission personnalisée pour notre système d'authentification par session
    """
    def has_permission(self, request, view):
        return bool(request.session.get('user_id'))

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        return bool(user_role == "admin")

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        return bool(user_role == "agent")

class IsDemandeur(BasePermission):
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        return bool(user_role == "demandeur")

class IsAdminOrAgent(BasePermission):
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        return bool(user_role in ("admin", "agent"))

class IsOwnerOrReadOnly(BasePermission):
    """
    Pour DemandeSubvention : le demandeur voit/édite uniquement ses demandes
    Les agents/admins ont tous les droits.
    """
    def has_object_permission(self, request, view, obj):
        user_id = request.session.get('user_id')
        user_role = request.session.get('user_role')
        
        if request.method in SAFE_METHODS:
            return (
                obj.utilisateur_id == user_id
                or user_role in ("agent", "admin")
            )
        return (
            obj.utilisateur_id == user_id
            or user_role in ("agent", "admin")
        )

class IsOwnerOrAdminOrAgent(BasePermission):
    """
    Permission pour les objets qui appartiennent à l'utilisateur ou aux admins/agents
    """
    def has_object_permission(self, request, view, obj):
        user_id = request.session.get('user_id')
        user_role = request.session.get('user_role')
        
        # Si c'est un objet avec un utilisateur
        if hasattr(obj, 'utilisateur_id'):
            return (
                obj.utilisateur_id == user_id
                or user_role in ("admin", "agent")
            )
        
        # Si c'est un objet avec un agent
        if hasattr(obj, 'agent_id'):
            return (
                obj.agent_id == user_id
                or user_role in ("admin", "agent")
            )
        
        return user_role in ("admin", "agent")

class CanCreateNotification(BasePermission):
    """
    Seuls les agents et admins peuvent créer des notifications
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            user_role = request.session.get('user_role')
            return bool(user_role in ("admin", "agent"))
        return True

class CanManagePaiements(BasePermission):
    """
    Seuls les agents peuvent gérer les paiements
    """
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        return bool(user_role in ("admin", "agent"))

class CanManageRapports(BasePermission):
    """
    Seuls les agents peuvent gérer les rapports
    """
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        return bool(user_role in ("admin", "agent"))

class CanViewOwnData(BasePermission):
    """
    Les utilisateurs ne peuvent voir que leurs propres données
    """
    def has_permission(self, request, view):
        user_role = request.session.get('user_role')
        if user_role == "demandeur":
            # Les demandeurs ne peuvent voir que leurs propres données
            return True
        return True  # Les agents et admins peuvent tout voir

    def has_object_permission(self, request, view, obj):
        user_id = request.session.get('user_id')
        user_role = request.session.get('user_role')
        
        if user_role == "demandeur":
            # Vérifier si l'objet appartient à l'utilisateur
            if hasattr(obj, 'utilisateur_id'):
                return obj.utilisateur_id == user_id
            if hasattr(obj, 'utilisateur'):
                return obj.utilisateur.id == user_id
        
        return True  # Les agents et admins peuvent tout voir



# from rest_framework.permissions import BasePermission, SAFE_METHODS

# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return bool(request.user and request.user.is_authenticated and request.user.role == "admin")

# class IsAgent(BasePermission):
#     def has_permission(self, request, view):
#         return bool(request.user and request.user.is_authenticated and request.user.role == "agent")

# class IsDemandeur(BasePermission):
#     def has_permission(self, request, view):
#         return bool(request.user and request.user.is_authenticated and request.user.role == "demandeur")

# class IsOwnerOrReadOnly(BasePermission):
#     """
#     Pour DossierDemande : le demandeur voit/édite uniquement ses dossiers
#     Les agents/admins ont tous les droits.
#     """
#     def has_object_permission(self, request, view, obj):
#         if request.method in SAFE_METHODS:
#             return (
#                 obj.utilisateur_id == request.user.id
#                 or request.user.role in ("agent", "admin")
#             )
#         return (
#             obj.utilisateur_id == request.user.id
#             or request.user.role in ("agent", "admin")
#         )
