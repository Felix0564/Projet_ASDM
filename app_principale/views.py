from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import CustomUser, DossierDemande, SuiviDossier, Notification
from .serializers import (
    UserCreateSerializer, UserPublicSerializer,
    DossierDemandeSerializer, DossierDemandeUpdateStatutSerializer,
    SuiviDossierSerializer, NotificationSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdmin, IsAgent

# ---- Utilisateurs ----
class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = CustomUser.objects.all().order_by("-date_joined")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "username", "first_name", "last_name", "phone", "role"]
    ordering_fields = ["date_joined", "last_login"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [AllowAny()]
        elif self.action in ["list"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserPublicSerializer

    @action(methods=["get"], detail=False, url_path="me")
    def me(self, request):
        return Response(UserPublicSerializer(request.user).data)

# ---- Dossiers ----
class DossierDemandeViewSet(viewsets.ModelViewSet):
    queryset = DossierDemande.objects.select_related("utilisateur").all().order_by("-date_depot")
    serializer_class = DossierDemandeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type_subvention", "statut", "utilisateur"]
    search_fields = ["description_projet"]
    ordering_fields = ["date_depot", "montant_demande"]

    def perform_create(self, serializer):
        # le demandeur est automatiquement le user courant s'il n'envoie pas utilisateur_id
        utilisateur = serializer.validated_data.get("utilisateur", self.request.user)
        serializer.save(utilisateur=utilisateur)

    @action(methods=["patch"], detail=True, url_path="statut")
    def update_statut(self, request, pk=None):
        """
        Agents/Admins peuvent changer le statut.
        """
        if not (request.user.role in ("agent", "admin")):
            return Response({"detail": "Non autorisé."}, status=403)
        dossier = self.get_object()
        s = DossierDemandeUpdateStatutSerializer(dossier, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(DossierDemandeSerializer(dossier).data)

# ---- Suivi ----
class SuiviDossierViewSet(viewsets.ModelViewSet):
    queryset = SuiviDossier.objects.select_related("dossier").all().order_by("-date_update")
    serializer_class = SuiviDossierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["dossier", "statut"]
    ordering_fields = ["date_update"]

    def create(self, request, *args, **kwargs):
        # Seulement agent/admin
        if not (request.user.role in ("agent", "admin")):
            return Response({"detail": "Non autorisé."}, status=403)
        return super().create(request, *args, **kwargs)

# ---- Notifications ----
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related("utilisateur").all().order_by("-date_envoi")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["utilisateur", "type", "statut"]
    ordering_fields = ["date_envoi"]
    search_fields = ["message"]

    def get_queryset(self):
        # un demandeur ne voit que ses notifications
        qs = super().get_queryset()
        if self.request.user.role == "demandeur":
            return qs.filter(utilisateur=self.request.user)
        return qs

    def perform_create(self, serializer):
        # Par défaut, l'émetteur est un agent/admin qui choisit le destinataire via utilisateur_id
        if not (self.request.user.role in ("agent", "admin")):
            raise PermissionError("Non autorisé.")
        serializer.save()
