from rest_framework import serializers
from .models import (
    Utilisateur, AgentASDM, DemandeSubvention, 
    Paiement, Document, Rapport, Notification
)
from django.contrib.auth.password_validation import validate_password

class UtilisateurCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = Utilisateur
        fields = ("id", "nom", "prenom", "email", "role", "password")
    
    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = Utilisateur(**validated_data)
        user.set_password(pwd)
        user.save()
        return user

class UtilisateurPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ("id", "nom", "prenom", "email", "role", "date_creation")
        read_only_fields = fields

class UtilisateurUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Utilisateur
        fields = ("nom", "prenom", "email", "role", "password")

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance

class AgentASDMSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurPublicSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(), write_only=True, source='utilisateur'
    )
    
    class Meta:
        model = AgentASDM
        fields = ("id", "utilisateur", "utilisateur_id", "droits_validation", "fonction", "departement")
        read_only_fields = ("id",)

class DocumentSerializer(serializers.ModelSerializer):
    demande_subvention_id = serializers.PrimaryKeyRelatedField(
        queryset=DemandeSubvention.objects.all(), write_only=True, source='demande_subvention', required=False
    )
    class Meta:
        model = Document
        fields = ("id", "nom", "type", "chemin_fichier", "date_upload", "taille_fichier", "demande_subvention_id")
        read_only_fields = ("id", "date_upload", "taille_fichier")

    def create(self, validated_data):
        file_field = validated_data.get("chemin_fichier")
        if file_field is not None and hasattr(file_field, "size"):
            validated_data["taille_fichier"] = file_field.size
        return super().create(validated_data)

class PaiementSerializer(serializers.ModelSerializer):
    demande_subvention_id = serializers.PrimaryKeyRelatedField(
        queryset=DemandeSubvention.objects.all(), write_only=True, source='demande_subvention'
    )
    class Meta:
        model = Paiement
        fields = ("id", "montant", "date_paiement", "mode_paiement", "reference", "statut", "demande_subvention_id")
        read_only_fields = ("id", "date_paiement")

class DemandeSubventionSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurPublicSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(), write_only=True, source='utilisateur', required=False
    )
    documents = DocumentSerializer(many=True, read_only=True)
    paiement = PaiementSerializer(read_only=True)
    # Modification : agent_traitant est maintenant un Utilisateur avec rôle agent
    agent_traitant = UtilisateurPublicSerializer(read_only=True)
    agent_traitant_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.filter(role='agent'), write_only=True, 
        source='agent_traitant', required=False
    )
    
    class Meta:
        model = DemandeSubvention
        fields = (
            "id", "type", "montant", "statut", "date_soumission", 
            "date_traitement", "commentaires", "utilisateur", "utilisateur_id",
            "agent_traitant", "agent_traitant_id", "documents", "paiement"
        )
        read_only_fields = ("id", "date_soumission", "date_traitement")

class DemandeSubventionUpdateStatutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeSubvention
        fields = ("statut", "commentaires")

class DemandeSubventionAssignerAgentSerializer(serializers.ModelSerializer):
    agent_traitant_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.filter(role='agent'), 
        source='agent_traitant', 
        write_only=True
    )
    
    class Meta:
        model = DemandeSubvention
        fields = ("agent_traitant_id",)
    
    def validate_agent_traitant_id(self, value):
        if value.role != 'agent':
            raise serializers.ValidationError("L'utilisateur doit avoir le rôle 'agent'")
        return value

# ===== SERIALIZERS DASHBOARD =====

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du dashboard"""
    utilisateurs = serializers.DictField()
    demandes = serializers.DictField()
    financier = serializers.DictField()
    documents = serializers.DictField()
    paiements = serializers.DictField()
    notifications = serializers.DictField()

class DashboardGraphsSerializer(serializers.Serializer):
    """Serializer pour les graphiques du dashboard"""
    evolution_demandes = serializers.ListField()
    repartition_type = serializers.ListField()
    repartition_statut = serializers.ListField()
    performance_agents = serializers.ListField()
    montants_par_mois = serializers.ListField()

class DashboardMetricsSerializer(serializers.Serializer):
    """Serializer pour les métriques du dashboard"""
    taux_acceptation = serializers.FloatField()
    temps_moyen_traitement_jours = serializers.IntegerField()
    montant_max_demande = serializers.DecimalField(max_digits=10, decimal_places=2)
    montant_moyen_demande = serializers.DecimalField(max_digits=10, decimal_places=2)
    agents_les_plus_actifs = serializers.ListField()

class DashboardDemandeSubventionListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de demandes dans le dashboard"""
    utilisateur_nom = serializers.CharField(source='utilisateur.prenom', read_only=True)
    utilisateur_email = serializers.CharField(source='utilisateur.email', read_only=True)
    agent_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = DemandeSubvention
        fields = (
            "id", "type", "montant", "statut", "date_soumission", 
            "utilisateur_nom", "utilisateur_email", "agent_nom"
        )
    
    def get_agent_nom(self, obj):
        if obj.agent_traitant:
            return f"{obj.agent_traitant.prenom} {obj.agent_traitant.nom}"
        return None

class DashboardUtilisateurListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes d'utilisateurs dans le dashboard"""
    nb_demandes = serializers.SerializerMethodField()
    
    class Meta:
        model = Utilisateur
        fields = ("id", "prenom", "nom", "email", "role", "date_creation", "nb_demandes")
    
    def get_nb_demandes(self, obj):
        if obj.role == 'demandeur':
            return obj.demandes_subvention.count()
        elif obj.role == 'agent':
            return obj.demandes_traitees.count()
        return 0

class DashboardDocumentListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de documents dans le dashboard"""
    demande_id = serializers.IntegerField(source='demande_subvention.id', read_only=True)
    utilisateur_nom = serializers.CharField(source='demande_subvention.utilisateur.prenom', read_only=True)
    
    class Meta:
        model = Document
        fields = ("id", "nom", "type", "date_upload", "taille_fichier", "demande_id", "utilisateur_nom")

class DashboardPaiementListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de paiements dans le dashboard"""
    demande_id = serializers.IntegerField(source='demande_subvention.id', read_only=True)
    utilisateur_nom = serializers.CharField(source='demande_subvention.utilisateur.prenom', read_only=True)
    
    class Meta:
        model = Paiement
        fields = ("id", "montant", "mode_paiement", "statut", "date_paiement", "reference", "demande_id", "utilisateur_nom")

class DashboardNotificationListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de notifications dans le dashboard"""
    utilisateur_nom = serializers.CharField(source='utilisateur.prenom', read_only=True)
    
    class Meta:
        model = Notification
        fields = ("id", "type", "contenu", "date_envoi", "lu", "priorite", "utilisateur_nom")

class DashboardAgentStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'un agent"""
    agent = AgentASDMSerializer()
    total_demandes = serializers.IntegerField()
    demandes_acceptees = serializers.IntegerField()
    demandes_refusees = serializers.IntegerField()
    taux_acceptation = serializers.FloatField()
    montant_total = serializers.DecimalField(max_digits=10, decimal_places=2)

class RapportSerializer(serializers.ModelSerializer):
    agent = AgentASDMSerializer(read_only=True)
    
    class Meta:
        model = Rapport
        fields = ("id", "periode", "date_generation", "statistiques", 
                 "format", "contenu", "agent")
        read_only_fields = ("id", "date_generation")

class NotificationSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurPublicSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(), write_only=True, source='utilisateur'
    )
    
    class Meta:
        model = Notification
        fields = ("id", "type", "contenu", "date_envoi", "lu", "priorite", 
                 "utilisateur", "utilisateur_id")
        read_only_fields = ("id", "date_envoi")

# from rest_framework import serializers
# from .models import CustomUser, DossierDemande, SuiviDossier, Notification
# from django.contrib.auth.password_validation import validate_password

# class UserCreateSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, validators=[validate_password])
#     class Meta:
#         model = CustomUser
#         fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "password")

#     def create(self, validated_data):
#         pwd = validated_data.pop("password")
#         user = CustomUser(**validated_data)
#         user.set_password(pwd)
#         user.save()
#         return user

# class UserPublicSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "date_joined", "last_login")
#         read_only_fields = fields

# class DossierDemandeSerializer(serializers.ModelSerializer):
#     utilisateur = UserPublicSerializer(read_only=True)
#     utilisateur_id = serializers.PrimaryKeyRelatedField(
#         queryset=CustomUser.objects.all(), write_only=True, source='utilisateur'
#     )
#     class Meta:
#         model = DossierDemande
#         fields = (
#             "id", "utilisateur", "utilisateur_id", "type_subvention", "montant_demande",
#             "description_projet", "fichiers", "date_depot", "statut"
#         )
#         read_only_fields = ("id", "utilisateur", "date_depot", "statut")

# class DossierDemandeUpdateStatutSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DossierDemande
#         fields = ("statut",)

# class SuiviDossierSerializer(serializers.ModelSerializer):
#     dossier_id = serializers.PrimaryKeyRelatedField(
#         queryset=DossierDemande.objects.all(), write_only=True, source="dossier"
#     )
#     class Meta:
#         model = SuiviDossier
#         fields = ("id", "dossier_id", "date_update", "commentaire", "statut")
#         read_only_fields = ("id", "date_update")

# class NotificationSerializer(serializers.ModelSerializer):
#     utilisateur = UserPublicSerializer(read_only=True)
#     utilisateur_id = serializers.PrimaryKeyRelatedField(
#         queryset=CustomUser.objects.all(), write_only=True, source='utilisateur'
#     )
#     class Meta:
#         model = Notification
#         fields = ("id", "utilisateur", "utilisateur_id", "message", "type", "statut", "date_envoi")
#         read_only_fields = ("id", "utilisateur", "date_envoi")
