from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import (
    Utilisateur, AgentASDM, DemandeSubvention, 
    Paiement, Document, Rapport, Notification
)
from .serializers import (
    UtilisateurCreateSerializer, UtilisateurPublicSerializer, AgentASDMSerializer,
    DemandeSubventionSerializer, DemandeSubventionUpdateStatutSerializer,
    DocumentSerializer, PaiementSerializer, RapportSerializer, NotificationSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdmin, IsAgent, IsAuthenticatedCustom

# ---- Authentification personnalisée ----
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Connexion avec email et mot de passe utilisant notre modèle Utilisateur
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Email et mot de passe requis'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authentification avec notre backend personnalisé
    from .auth_backend import UtilisateurAuthBackend
    backend = UtilisateurAuthBackend()
    user = backend.authenticate(request, email=email, password=password)
    
    if user is not None:
        # Créer une session pour l'utilisateur
        request.session['user_id'] = user.id
        request.session['user_email'] = user.email
        request.session['user_role'] = user.role
        
        return Response({
            'message': 'Connexion réussie',
            'user': UtilisateurPublicSerializer(user).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Email ou mot de passe incorrect'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def logout_view(request):
    """
    Déconnexion
    """
    request.session.flush()
    return Response({
        'message': 'Déconnexion réussie'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def user_profile(request):
    """
    Profil de l'utilisateur connecté
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'error': 'Non authentifié'}, status=401)
    
    try:
        user = Utilisateur.objects.get(id=user_id)
        return Response(UtilisateurPublicSerializer(user).data)
    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=404)

# ---- Middleware personnalisé pour l'authentification ----
class UtilisateurAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            try:
                request.user = Utilisateur.objects.get(id=user_id)
            except Utilisateur.DoesNotExist:
                request.user = None
        else:
            request.user = None
        
        response = self.get_response(request)
        return response

# ---- Utilisateurs ----
class UtilisateurViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = Utilisateur.objects.all().order_by("-date_creation")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "prenom", "nom", "role"]
    ordering_fields = ["date_creation"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [AllowAny()]
        elif self.action in ["list"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UtilisateurCreateSerializer
        return UtilisateurPublicSerializer

    @action(methods=["get"], detail=False, url_path="me")
    def me(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            try:
                user = Utilisateur.objects.get(id=user_id)
                return Response(UtilisateurPublicSerializer(user).data)
            except Utilisateur.DoesNotExist:
                return Response({'error': 'Utilisateur non trouvé'}, status=404)
        return Response({'error': 'Non authentifié'}, status=401)

# ---- Agents ASDM ----
class AgentASDMViewSet(viewsets.ModelViewSet):
    queryset = AgentASDM.objects.select_related("utilisateur").all().order_by("-utilisateur__date_creation")
    serializer_class = AgentASDMSerializer
    permission_classes = [IsAuthenticatedCustom, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["utilisateur__email", "utilisateur__prenom", "utilisateur__nom", "fonction", "departement"]
    ordering_fields = ["utilisateur__date_creation"]

    @action(methods=["post"], detail=True, url_path="valider-demande")
    def valider_demande(self, request, pk=None):
        """Valide une demande de subvention"""
        agent = self.get_object()
        demande_id = request.data.get('demande_id')
        try:
            demande = DemandeSubvention.objects.get(id=demande_id)
            agent.valider_demande(demande)
            return Response({"message": "Demande validée avec succès"})
        except DemandeSubvention.DoesNotExist:
            return Response({"error": "Demande non trouvée"}, status=404)

    @action(methods=["post"], detail=True, url_path="rejeter-demande")
    def rejeter_demande(self, request, pk=None):
        """Rejette une demande de subvention"""
        agent = self.get_object()
        demande_id = request.data.get('demande_id')
        try:
            demande = DemandeSubvention.objects.get(id=demande_id)
            agent.rejeter_demande(demande)
            return Response({"message": "Demande rejetée"})
        except DemandeSubvention.DoesNotExist:
            return Response({"error": "Demande non trouvée"}, status=404)

# ---- Demandes de Subvention ----
class DemandeSubventionViewSet(viewsets.ModelViewSet):
    queryset = DemandeSubvention.objects.select_related("utilisateur", "agent_traitant__utilisateur").all().order_by("-date_soumission")
    serializer_class = DemandeSubventionSerializer
    permission_classes = [IsAuthenticatedCustom, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "statut", "utilisateur", "agent_traitant"]
    search_fields = ["commentaires"]
    ordering_fields = ["date_soumission", "montant"]

    def perform_create(self, serializer):
        user_id = self.request.session.get('user_id')
        if user_id:
            utilisateur = Utilisateur.objects.get(id=user_id)
            serializer.save(utilisateur=utilisateur)

    @action(methods=["patch"], detail=True, url_path="statut")
    def update_statut(self, request, pk=None):
        """Agents/Admins peuvent changer le statut"""
        user_role = request.session.get('user_role')
        if not (user_role in ("agent", "admin")):
            return Response({"detail": "Non autorisé."}, status=403)
        demande = self.get_object()
        s = DemandeSubventionUpdateStatutSerializer(demande, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(DemandeSubventionSerializer(demande).data)

    @action(methods=["post"], detail=True, url_path="ajouter-document")
    def ajouter_document(self, request, pk=None):
        """Ajoute un document à la demande"""
        demande = self.get_object()
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(demande_subvention=demande)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

# ---- Documents ----
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("demande_subvention").all().order_by("-date_upload")
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticatedCustom]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["type", "demande_subvention"]
    ordering_fields = ["date_upload", "taille_fichier"]

# ---- Paiements ----
class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.select_related("demande_subvention").all().order_by("-date_paiement")
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticatedCustom, IsAgent]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["statut", "mode_paiement", "demande_subvention"]
    ordering_fields = ["date_paiement", "montant"]

    @action(methods=["post"], detail=True, url_path="traiter")
    def traiter_paiement(self, request, pk=None):
        """Traite un paiement"""
        paiement = self.get_object()
        paiement.traiter()
        return Response({"message": "Paiement traité avec succès"})

    @action(methods=["post"], detail=True, url_path="annuler")
    def annuler_paiement(self, request, pk=None):
        """Annule un paiement"""
        paiement = self.get_object()
        paiement.annuler()
        return Response({"message": "Paiement annulé"})

# ---- Rapports ----
class RapportViewSet(viewsets.ModelViewSet):
    queryset = Rapport.objects.select_related("agent__utilisateur").all().order_by("-date_generation")
    serializer_class = RapportSerializer
    permission_classes = [IsAuthenticatedCustom, IsAgent]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["format", "agent", "periode"]
    ordering_fields = ["date_generation"]

    def perform_create(self, serializer):
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                agent = AgentASDM.objects.get(utilisateur_id=user_id)
                serializer.save(agent=agent)
            except AgentASDM.DoesNotExist:
                return Response({"error": "Utilisateur n'est pas un agent"}, status=400)

# ---- Notifications ----
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related("utilisateur").all().order_by("-date_envoi")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedCustom]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["utilisateur", "type", "lu", "priorite"]
    ordering_fields = ["date_envoi"]
    search_fields = ["contenu"]

    def get_queryset(self):
        qs = super().get_queryset()
        user_role = self.request.session.get('user_role')
        if user_role == "demandeur":
            user_id = self.request.session.get('user_id')
            return qs.filter(utilisateur_id=user_id)
        return qs

    def perform_create(self, serializer):
        user_role = self.request.session.get('user_role')
        if not (user_role in ("agent", "admin")):
            raise PermissionError("Non autorisé.")
        serializer.save()

    @action(methods=["post"], detail=True, url_path="marquer-lu")
    def marquer_lu(self, request, pk=None):
        """Marque une notification comme lue"""
        notification = self.get_object()
        notification.marquer_lu()
        return Response({"message": "Notification marquée comme lue"})

@api_view(['GET'])
def api_home(request):
    """
    Vue d'accueil de l'API ASDM
    """
    return Response({
        'message': 'Bienvenue sur l\'API ASDM Backend',
        'status': 'active',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'profile': '/api/auth/profile/',
            },
            'utilisateurs': '/api/utilisateurs/',
            'agents': '/api/agents/',
            'demandes': '/api/demandes/',
            'documents': '/api/documents/',
            'paiements': '/api/paiements/',
            'rapports': '/api/rapports/',
            'notifications': '/api/notifications/',
            'admin': '/admin/',
        }
    }, status=status.HTTP_200_OK)




# from rest_framework import viewsets, mixins, status, filters
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.permissions import AllowAny, IsAuthenticated

# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status

# from .models import CustomUser, DossierDemande, SuiviDossier, Notification
# from .serializers import (
#     UserCreateSerializer, UserPublicSerializer,
#     DossierDemandeSerializer, DossierDemandeUpdateStatutSerializer,
#     SuiviDossierSerializer, NotificationSerializer
# )
# from .permissions import IsOwnerOrReadOnly, IsAdmin, IsAgent

# # ---- Utilisateurs ----
# class UserViewSet(mixins.CreateModelMixin,
#                   mixins.RetrieveModelMixin,
#                   mixins.ListModelMixin,
#                   viewsets.GenericViewSet):
#     queryset = CustomUser.objects.all().order_by("-date_joined")
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ["email", "username", "first_name", "last_name", "phone", "role"]
#     ordering_fields = ["date_joined", "last_login"]

#     def get_permissions(self):
#         if self.action in ["create"]:
#             return [AllowAny()]
#         elif self.action in ["list"]:
#             return [IsAuthenticated(), IsAdmin()]
#         return [IsAuthenticated()]

#     def get_serializer_class(self):
#         if self.action == "create":
#             return UserCreateSerializer
#         return UserPublicSerializer

#     @action(methods=["get"], detail=False, url_path="me")
#     def me(self, request):
#         return Response(UserPublicSerializer(request.user).data)

# # ---- Dossiers ----
# class DossierDemandeViewSet(viewsets.ModelViewSet):
#     queryset = DossierDemande.objects.select_related("utilisateur").all().order_by("-date_depot")
#     serializer_class = DossierDemandeSerializer
#     permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ["type_subvention", "statut", "utilisateur"]
#     search_fields = ["description_projet"]
#     ordering_fields = ["date_depot", "montant_demande"]

#     def perform_create(self, serializer):
#         # le demandeur est automatiquement le user courant s'il n'envoie pas utilisateur_id
#         utilisateur = serializer.validated_data.get("utilisateur", self.request.user)
#         serializer.save(utilisateur=utilisateur)

#     @action(methods=["patch"], detail=True, url_path="statut")
#     def update_statut(self, request, pk=None):
#         """
#         Agents/Admins peuvent changer le statut.
#         """
#         if not (request.user.role in ("agent", "admin")):
#             return Response({"detail": "Non autorisé."}, status=403)
#         dossier = self.get_object()
#         s = DossierDemandeUpdateStatutSerializer(dossier, data=request.data, partial=True)
#         s.is_valid(raise_exception=True)
#         s.save()
#         return Response(DossierDemandeSerializer(dossier).data)

# # ---- Suivi ----
# class SuiviDossierViewSet(viewsets.ModelViewSet):
#     queryset = SuiviDossier.objects.select_related("dossier").all().order_by("-date_update")
#     serializer_class = SuiviDossierSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_fields = ["dossier", "statut"]
#     ordering_fields = ["date_update"]

#     def create(self, request, *args, **kwargs):
#         # Seulement agent/admin
#         if not (request.user.role in ("agent", "admin")):
#             return Response({"detail": "Non autorisé."}, status=403)
#         return super().create(request, *args, **kwargs)

# # ---- Notifications ----
# class NotificationViewSet(viewsets.ModelViewSet):
#     queryset = Notification.objects.select_related("utilisateur").all().order_by("-date_envoi")
#     serializer_class = NotificationSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
#     filterset_fields = ["utilisateur", "type", "statut"]
#     ordering_fields = ["date_envoi"]
#     search_fields = ["message"]

#     def get_queryset(self):
#         # un demandeur ne voit que ses notifications
#         qs = super().get_queryset()
#         if self.request.user.role == "demandeur":
#             return qs.filter(utilisateur=self.request.user)
#         return qs

#     def perform_create(self, serializer):
#         # Par défaut, l'émetteur est un agent/admin qui choisit le destinataire via utilisateur_id
#         if not (self.request.user.role in ("agent", "admin")):
#             raise PermissionError("Non autorisé.")
#         serializer.save()

# @api_view(['GET'])
# def api_home(request):
#     """
#     Vue d'accueil de l'API ASDM
#     """
#     return Response({
#         'message': 'Bienvenue sur l\'API ASDM Backend',
#         'status': 'active',
#         'version': '1.0.0',
#         'endpoints': {
#             'users': '/api/users/',
#             'dossiers': '/api/dossiers/',
#             'suivis': '/api/suivis/',
#             'notifications': '/api/notifications/',
#             'admin': '/admin/',
#         }
#     }, status=status.HTTP_200_OK)