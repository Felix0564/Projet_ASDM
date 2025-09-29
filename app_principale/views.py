from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Utilisateur, AgentASDM, DemandeSubvention, 
    Paiement, Document, Rapport, Notification
)
from .serializers import (
    UtilisateurCreateSerializer, UtilisateurPublicSerializer, UtilisateurUpdateSerializer, AgentASDMSerializer,
    DemandeSubventionSerializer, DemandeSubventionUpdateStatutSerializer, DemandeSubventionAssignerAgentSerializer,
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
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    queryset = Utilisateur.objects.all().order_by("-date_creation")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "prenom", "nom", "role"]
    ordering_fields = ["date_creation"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return UtilisateurCreateSerializer
        if self.action in ("update", "partial_update"):
            return UtilisateurUpdateSerializer
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

    def perform_destroy(self, instance):
        """
        Supprime l'utilisateur et gère les relations automatiquement.
        Les relations CASCADE dans les modèles s'occuperont de la suppression
        des objets liés (AgentASDM, DemandeSubvention, Notifications, etc.)
        """
        # Vérifier si l'utilisateur a des demandes en cours
        demandes_en_cours = instance.demandes_subvention.filter(
            statut__in=['en_attente', 'en_etude']
        ).exists()
        
        if demandes_en_cours:
            # Optionnel: empêcher la suppression si des demandes sont en cours
            # raise ValidationError("Impossible de supprimer un utilisateur avec des demandes en cours")
            pass
        
        # Supprimer l'utilisateur (les relations CASCADE s'occuperont du reste)
        instance.delete()

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

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

# ---- Demandes de Subvention ----
class DemandeSubventionViewSet(viewsets.ModelViewSet):
    queryset = DemandeSubvention.objects.select_related("utilisateur", "agent_traitant").all().order_by("-date_soumission")
    serializer_class = DemandeSubventionSerializer
    permission_classes = [IsAuthenticatedCustom, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "statut", "utilisateur", "agent_traitant"]
    search_fields = ["commentaires"]
    ordering_fields = ["date_soumission", "montant"]

    def perform_create(self, serializer):
        # Respecte un utilisateur_id fourni, sinon fallback session
        utilisateur_obj = None
        utilisateur_from_request = self.request.data.get('utilisateur_id')
        if utilisateur_from_request:
            try:
                utilisateur_obj = Utilisateur.objects.get(id=utilisateur_from_request)
            except Utilisateur.DoesNotExist:
                pass
        if utilisateur_obj is None:
            user_id = self.request.session.get('user_id')
            if user_id:
                utilisateur_obj = Utilisateur.objects.get(id=user_id)
        if utilisateur_obj is not None:
            serializer.save(utilisateur=utilisateur_obj)
        else:
            serializer.save()

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

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
    
    @action(methods=["post"], detail=True, url_path="assigner-agent")
    def assigner_agent(self, request, pk=None):
        """Assigne un utilisateur avec le rôle agent à la demande"""
        user_role = request.session.get('user_role')
        if not (user_role in ("agent", "admin")):
            return Response({"detail": "Non autorisé. Seuls les agents et admins peuvent assigner des agents."}, status=403)
        
        demande = self.get_object()
        serializer = DemandeSubventionAssignerAgentSerializer(demande, data=request.data, partial=True)
        
        if serializer.is_valid():
            try:
                # Utiliser la méthode du modèle pour assigner l'agent
                demande.assigner_agent(serializer.validated_data['agent_traitant'])
                return Response({
                    "message": f"Agent assigné avec succès à la demande {demande.id}",
                    "demande": DemandeSubventionSerializer(demande).data
                }, status=200)
            except ValueError as e:
                return Response({"error": str(e)}, status=400)
        
        return Response(serializer.errors, status=400)

# ---- Documents ----
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("demande_subvention").all().order_by("-date_upload")
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticatedCustom]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["type", "demande_subvention"]
    ordering_fields = ["date_upload", "taille_fichier"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

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

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

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

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

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

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

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
            'api': {
                'utilisateurs': '/api/utilisateurs/',
                'agents': '/api/agents/',
                'demandes': '/api/demandes/',
                'documents': '/api/documents/',
                'paiements': '/api/paiements/',
                'rapports': '/api/rapports/',
                'notifications': '/api/notifications/',
            },
            'dashboard': {
                'stats': '/dashboard/stats/',
                'graphs': '/dashboard/graphs/',
                'metrics': '/dashboard/metrics/',
                'utilisateurs': '/dashboard/utilisateurs/',
                'demandes': '/dashboard/demandes/',
                'agents': '/dashboard/agents/',
                'documents': '/dashboard/documents/',
                'paiements': '/dashboard/paiements/',
                'notifications': '/dashboard/notifications/',
            },
            'admin': '/admin/',
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def agents_disponibles(request):
    """
    Retourne la liste des utilisateurs avec le rôle agent disponibles pour assignation
    """
    agents = Utilisateur.objects.filter(role='agent').values('id', 'prenom', 'nom', 'email')
    return Response({
        'agents_disponibles': list(agents),
        'total': agents.count()
    }, status=status.HTTP_200_OK)

# ===== API DASHBOARD =====

@api_view(['GET'])
def dashboard_stats(request):
    """
    Statistiques générales pour le dashboard
    """
    # Statistiques des utilisateurs
    total_utilisateurs = Utilisateur.objects.count()
    total_agents = Utilisateur.objects.filter(role='agent').count()
    total_admins = Utilisateur.objects.filter(role='admin').count()
    total_demandeurs = Utilisateur.objects.filter(role='demandeur').count()
    
    # Statistiques des demandes
    total_demandes = DemandeSubvention.objects.count()
    demandes_en_attente = DemandeSubvention.objects.filter(statut='en_attente').count()
    demandes_en_etude = DemandeSubvention.objects.filter(statut='en_etude').count()
    demandes_acceptees = DemandeSubvention.objects.filter(statut='accepte').count()
    demandes_refusees = DemandeSubvention.objects.filter(statut='refuse').count()
    
    # Statistiques financières
    montant_total_demande = DemandeSubvention.objects.aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    montant_total_paye = Paiement.objects.filter(statut='traite').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Statistiques des documents
    total_documents = Document.objects.count()
    
    # Statistiques des paiements
    total_paiements = Paiement.objects.count()
    paiements_en_attente = Paiement.objects.filter(statut='en_attente').count()
    paiements_traites = Paiement.objects.filter(statut='traite').count()
    
    # Statistiques des notifications
    notifications_non_lues = Notification.objects.filter(lu=False).count()
    
    # Demandes des 30 derniers jours
    date_limite = timezone.now() - timedelta(days=30)
    demandes_30_jours = DemandeSubvention.objects.filter(
        date_soumission__gte=date_limite
    ).count()
    
    return Response({
        'utilisateurs': {
            'total': total_utilisateurs,
            'agents': total_agents,
            'admins': total_admins,
            'demandeurs': total_demandeurs
        },
        'demandes': {
            'total': total_demandes,
            'en_attente': demandes_en_attente,
            'en_etude': demandes_en_etude,
            'acceptees': demandes_acceptees,
            'refusees': demandes_refusees,
            'derniers_30_jours': demandes_30_jours
        },
        'financier': {
            'montant_total_demande': float(montant_total_demande),
            'montant_total_paye': float(montant_total_paye),
            'montant_en_cours': float(montant_total_demande - montant_total_paye)
        },
        'documents': {
            'total': total_documents
        },
        'paiements': {
            'total': total_paiements,
            'en_attente': paiements_en_attente,
            'traites': paiements_traites
        },
        'notifications': {
            'non_lues': notifications_non_lues
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def dashboard_graphs(request):
    """
    Données pour les graphiques du dashboard
    """
    # Évolution des demandes par mois (12 derniers mois)
    date_limite = timezone.now() - timedelta(days=365)
    demandes_par_mois = DemandeSubvention.objects.filter(
        date_soumission__gte=date_limite
    ).annotate(
        mois=TruncMonth('date_soumission')
    ).values('mois').annotate(
        total=Count('id')
    ).order_by('mois')
    
    # Répartition par type de subvention
    demandes_par_type = DemandeSubvention.objects.values('type').annotate(
        total=Count('id'),
        montant_total=Sum('montant')
    ).order_by('-total')
    
    # Répartition par statut
    demandes_par_statut = DemandeSubvention.objects.values('statut').annotate(
        total=Count('id')
    ).order_by('statut')
    
    # Performance des agents (top 10)
    performance_agents = DemandeSubvention.objects.filter(
        agent_traitant__isnull=False
    ).values(
        'agent_traitant__prenom',
        'agent_traitant__nom',
        'agent_traitant__email'
    ).annotate(
        total_traitees=Count('id'),
        total_acceptees=Count('id', filter=Q(statut='accepte')),
        total_refusees=Count('id', filter=Q(statut='refuse'))
    ).order_by('-total_traitees')[:10]
    
    # Montants par mois
    montants_par_mois = DemandeSubvention.objects.filter(
        date_soumission__gte=date_limite
    ).annotate(
        mois=TruncMonth('date_soumission')
    ).values('mois').annotate(
        montant_total=Sum('montant')
    ).order_by('mois')
    
    return Response({
        'evolution_demandes': list(demandes_par_mois),
        'repartition_type': list(demandes_par_type),
        'repartition_statut': list(demandes_par_statut),
        'performance_agents': list(performance_agents),
        'montants_par_mois': list(montants_par_mois)
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def dashboard_metrics(request):
    """
    Métriques détaillées pour le dashboard
    """
    # Taux d'acceptation global
    total_demandes_traitees = DemandeSubvention.objects.filter(
        statut__in=['accepte', 'refuse']
    ).count()
    
    total_acceptees = DemandeSubvention.objects.filter(statut='accepte').count()
    
    taux_acceptation = (total_acceptees / total_demandes_traitees * 100) if total_demandes_traitees > 0 else 0
    
    # Temps moyen de traitement (en jours)
    demandes_traitees = DemandeSubvention.objects.filter(
        date_traitement__isnull=False
    ).annotate(
        duree_traitement=F('date_traitement') - F('date_soumission')
    )
    
    temps_moyen = demandes_traitees.aggregate(
        temps_moyen=Avg('duree_traitement')
    )['temps_moyen']
    
    # Demande la plus élevée
    demande_max = DemandeSubvention.objects.aggregate(
        montant_max=Sum('montant')
    )['montant_max'] or 0
    
    # Demande moyenne
    demande_moyenne = DemandeSubvention.objects.aggregate(
        montant_moyen=Avg('montant')
    )['montant_moyen'] or 0
    
    # Agents les plus actifs
    agents_actifs = DemandeSubvention.objects.filter(
        agent_traitant__isnull=False
    ).values('agent_traitant').annotate(
        nb_demandes=Count('id')
    ).order_by('-nb_demandes')[:5]
    
    return Response({
        'taux_acceptation': round(taux_acceptation, 2),
        'temps_moyen_traitement_jours': temps_moyen.days if temps_moyen else 0,
        'montant_max_demande': float(demande_max),
        'montant_moyen_demande': float(demande_moyenne),
        'agents_les_plus_actifs': list(agents_actifs)
    }, status=status.HTTP_200_OK)

# ===== VUES CRUD DASHBOARD =====

class DashboardUtilisateurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs depuis le dashboard
    """
    queryset = Utilisateur.objects.all().order_by("-date_creation")
    serializer_class = UtilisateurPublicSerializer
    permission_classes = [IsAuthenticatedCustom, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "prenom", "nom", "role"]
    filterset_fields = ["role"]
    ordering_fields = ["date_creation", "prenom", "nom"]
    ordering = ["-date_creation"]

    def get_serializer_class(self):
        if self.action == "create":
            return UtilisateurCreateSerializer
        if self.action in ("update", "partial_update"):
            return UtilisateurUpdateSerializer
        return UtilisateurPublicSerializer

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    @action(methods=["get"], detail=False, url_path="agents")
    def list_agents(self, request):
        """Liste tous les agents"""
        agents = self.queryset.filter(role='agent')
        serializer = self.get_serializer(agents, many=True)
        return Response({
            'agents': serializer.data,
            'total': agents.count()
        })

    @action(methods=["get"], detail=False, url_path="demandeurs")
    def list_demandeurs(self, request):
        """Liste tous les demandeurs"""
        demandeurs = self.queryset.filter(role='demandeur')
        serializer = self.get_serializer(demandeurs, many=True)
        return Response({
            'demandeurs': serializer.data,
            'total': demandeurs.count()
        })

class DashboardDemandeSubventionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des demandes depuis le dashboard
    """
    queryset = DemandeSubvention.objects.select_related("utilisateur", "agent_traitant").all().order_by("-date_soumission")
    serializer_class = DemandeSubventionSerializer
    permission_classes = [IsAuthenticatedCustom]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "statut", "utilisateur", "agent_traitant"]
    search_fields = ["commentaires", "utilisateur__email", "utilisateur__prenom", "utilisateur__nom"]
    ordering_fields = ["date_soumission", "montant", "statut"]
    ordering = ["-date_soumission"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    def perform_create(self, serializer):
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                utilisateur = Utilisateur.objects.get(id=user_id)
                serializer.save(utilisateur=utilisateur)
            except Utilisateur.DoesNotExist:
                serializer.save()

    @action(methods=["get"], detail=False, url_path="en-attente")
    def list_en_attente(self, request):
        """Liste les demandes en attente"""
        demandes = self.queryset.filter(statut='en_attente')
        serializer = self.get_serializer(demandes, many=True)
        return Response({
            'demandes_en_attente': serializer.data,
            'total': demandes.count()
        })

    @action(methods=["get"], detail=False, url_path="en-etude")
    def list_en_etude(self, request):
        """Liste les demandes en cours d'étude"""
        demandes = self.queryset.filter(statut='en_etude')
        serializer = self.get_serializer(demandes, many=True)
        return Response({
            'demandes_en_etude': serializer.data,
            'total': demandes.count()
        })

    @action(methods=["get"], detail=False, url_path="acceptees")
    def list_acceptees(self, request):
        """Liste les demandes acceptées"""
        demandes = self.queryset.filter(statut='accepte')
        serializer = self.get_serializer(demandes, many=True)
        return Response({
            'demandes_acceptees': serializer.data,
            'total': demandes.count()
        })

    @action(methods=["get"], detail=False, url_path="refusees")
    def list_refusees(self, request):
        """Liste les demandes refusées"""
        demandes = self.queryset.filter(statut='refuse')
        serializer = self.get_serializer(demandes, many=True)
        return Response({
            'demandes_refusees': serializer.data,
            'total': demandes.count()
        })

    @action(methods=["post"], detail=True, url_path="assigner-agent")
    def assigner_agent(self, request, pk=None):
        """Assigne un agent à une demande"""
        demande = self.get_object()
        serializer = DemandeSubventionAssignerAgentSerializer(demande, data=request.data, partial=True)
        
        if serializer.is_valid():
            try:
                demande.assigner_agent(serializer.validated_data['agent_traitant'])
                return Response({
                    "message": f"Agent assigné avec succès à la demande {demande.id}",
                    "demande": DemandeSubventionSerializer(demande).data
                }, status=200)
            except ValueError as e:
                return Response({"error": str(e)}, status=400)
        
        return Response(serializer.errors, status=400)

    @action(methods=["post"], detail=True, url_path="valider")
    def valider_demande(self, request, pk=None):
        """Valide une demande"""
        demande = self.get_object()
        try:
            demande.valider_demande()
            return Response({
                "message": f"Demande {demande.id} validée avec succès",
                "demande": DemandeSubventionSerializer(demande).data
            }, status=200)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

    @action(methods=["post"], detail=True, url_path="rejeter")
    def rejeter_demande(self, request, pk=None):
        """Rejette une demande"""
        demande = self.get_object()
        try:
            demande.rejeter_demande()
            return Response({
                "message": f"Demande {demande.id} rejetée",
                "demande": DemandeSubventionSerializer(demande).data
            }, status=200)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

class DashboardAgentASDMViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des agents depuis le dashboard
    """
    queryset = AgentASDM.objects.select_related("utilisateur").all().order_by("-utilisateur__date_creation")
    serializer_class = AgentASDMSerializer
    permission_classes = [IsAuthenticatedCustom, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["utilisateur__email", "utilisateur__prenom", "utilisateur__nom", "fonction", "departement"]
    filterset_fields = ["droits_validation", "departement", "fonction"]
    ordering_fields = ["utilisateur__date_creation"]
    ordering = ["-utilisateur__date_creation"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    @action(methods=["get"], detail=True, url_path="demandes")
    def get_demandes_agent(self, request, pk=None):
        """Récupère les demandes assignées à cet agent"""
        agent = self.get_object()
        demandes = DemandeSubvention.objects.filter(agent_traitant=agent.utilisateur)
        serializer = DemandeSubventionSerializer(demandes, many=True)
        return Response({
            'demandes_agent': serializer.data,
            'total': demandes.count()
        })

    @action(methods=["get"], detail=True, url_path="statistiques")
    def get_statistiques_agent(self, request, pk=None):
        """Statistiques de l'agent"""
        agent = self.get_object()
        
        total_demandes = DemandeSubvention.objects.filter(agent_traitant=agent.utilisateur).count()
        demandes_acceptees = DemandeSubvention.objects.filter(
            agent_traitant=agent.utilisateur, 
            statut='accepte'
        ).count()
        demandes_refusees = DemandeSubvention.objects.filter(
            agent_traitant=agent.utilisateur, 
            statut='refuse'
        ).count()
        
        montant_total = DemandeSubvention.objects.filter(
            agent_traitant=agent.utilisateur
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        return Response({
            'agent': AgentASDMSerializer(agent).data,
            'total_demandes': total_demandes,
            'demandes_acceptees': demandes_acceptees,
            'demandes_refusees': demandes_refusees,
            'taux_acceptation': round((demandes_acceptees / total_demandes * 100) if total_demandes > 0 else 0, 2),
            'montant_total': float(montant_total)
        })

class DashboardDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des documents depuis le dashboard
    """
    queryset = Document.objects.select_related("demande_subvention").all().order_by("-date_upload")
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticatedCustom]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "demande_subvention"]
    search_fields = ["nom", "demande_subvention__utilisateur__email"]
    ordering_fields = ["date_upload", "taille_fichier"]
    ordering = ["-date_upload"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    @action(methods=["get"], detail=False, url_path="par-type")
    def list_by_type(self, request):
        """Liste les documents groupés par type"""
        documents_par_type = Document.objects.values('type').annotate(
            total=Count('id'),
            taille_totale=Sum('taille_fichier')
        ).order_by('-total')
        
        return Response({
            'documents_par_type': list(documents_par_type)
        })

class DashboardPaiementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des paiements depuis le dashboard
    """
    queryset = Paiement.objects.select_related("demande_subvention").all().order_by("-date_paiement")
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticatedCustom, IsAgent]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["statut", "mode_paiement", "demande_subvention"]
    ordering_fields = ["date_paiement", "montant"]
    ordering = ["-date_paiement"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    @action(methods=["get"], detail=False, url_path="en-attente")
    def list_en_attente(self, request):
        """Liste les paiements en attente"""
        paiements = self.queryset.filter(statut='en_attente')
        serializer = self.get_serializer(paiements, many=True)
        return Response({
            'paiements_en_attente': serializer.data,
            'total': paiements.count()
        })

    @action(methods=["post"], detail=True, url_path="traiter")
    def traiter_paiement(self, request, pk=None):
        """Traite un paiement"""
        paiement = self.get_object()
        paiement.traiter()
        return Response({
            "message": "Paiement traité avec succès",
            "paiement": PaiementSerializer(paiement).data
        })

class DashboardNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des notifications depuis le dashboard
    """
    queryset = Notification.objects.select_related("utilisateur").all().order_by("-date_envoi")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedCustom]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["utilisateur", "type", "lu", "priorite"]
    search_fields = ["contenu", "utilisateur__email"]
    ordering_fields = ["date_envoi", "priorite"]
    ordering = ["-date_envoi"]

    def get_permissions(self):
        # Mode développement: rendre toutes les actions publiques
        return [AllowAny()]

    def get_queryset(self):
        qs = super().get_queryset()
        user_role = self.request.session.get('user_role')
        if user_role == "demandeur":
            user_id = self.request.session.get('user_id')
            return qs.filter(utilisateur_id=user_id)
        return qs

    @action(methods=["get"], detail=False, url_path="non-lues")
    def list_non_lues(self, request):
        """Liste les notifications non lues"""
        notifications = self.get_queryset().filter(lu=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response({
            'notifications_non_lues': serializer.data,
            'total': notifications.count()
        })

    @action(methods=["post"], detail=True, url_path="marquer-lu")
    def marquer_lu(self, request, pk=None):
        """Marque une notification comme lue"""
        notification = self.get_object()
        notification.marquer_lu()
        return Response({
            "message": "Notification marquée comme lue",
            "notification": NotificationSerializer(notification).data
        })




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