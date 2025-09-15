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
    class Meta:
        model = Document
        fields = ("id", "nom", "type", "chemin_fichier", "date_upload", "taille_fichier")
        read_only_fields = ("id", "date_upload", "taille_fichier")

    def create(self, validated_data):
        file_field = validated_data.get("chemin_fichier")
        if file_field is not None and hasattr(file_field, "size"):
            validated_data["taille_fichier"] = file_field.size
        return super().create(validated_data)

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ("id", "montant", "date_paiement", "mode_paiement", "reference", "statut")
        read_only_fields = ("id", "date_paiement")

class DemandeSubventionSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurPublicSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(), write_only=True, source='utilisateur'
    )
    documents = DocumentSerializer(many=True, read_only=True)
    paiement = PaiementSerializer(read_only=True)
    agent_traitant = AgentASDMSerializer(read_only=True)
    
    class Meta:
        model = DemandeSubvention
        fields = (
            "id", "type", "montant", "statut", "date_soumission", 
            "date_traitement", "commentaires", "utilisateur", "utilisateur_id",
            "agent_traitant", "documents", "paiement"
        )
        read_only_fields = ("id", "date_soumission", "date_traitement", "agent_traitant")

class DemandeSubventionUpdateStatutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeSubvention
        fields = ("statut", "commentaires")

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
