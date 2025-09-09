from rest_framework import serializers
from .models import CustomUser, DossierDemande, SuiviDossier, Notification
from django.contrib.auth.password_validation import validate_password

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = CustomUser
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "password")

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(pwd)
        user.save()
        return user

class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "date_joined", "last_login")
        read_only_fields = fields

class DossierDemandeSerializer(serializers.ModelSerializer):
    utilisateur = UserPublicSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), write_only=True, source='utilisateur'
    )
    class Meta:
        model = DossierDemande
        fields = (
            "id", "utilisateur", "utilisateur_id", "type_subvention", "montant_demande",
            "description_projet", "fichiers", "date_depot", "statut"
        )
        read_only_fields = ("id", "utilisateur", "date_depot", "statut")

class DossierDemandeUpdateStatutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierDemande
        fields = ("statut",)

class SuiviDossierSerializer(serializers.ModelSerializer):
    dossier_id = serializers.PrimaryKeyRelatedField(
        queryset=DossierDemande.objects.all(), write_only=True, source="dossier"
    )
    class Meta:
        model = SuiviDossier
        fields = ("id", "dossier_id", "date_update", "commentaire", "statut")
        read_only_fields = ("id", "date_update")

class NotificationSerializer(serializers.ModelSerializer):
    utilisateur = UserPublicSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), write_only=True, source='utilisateur'
    )
    class Meta:
        model = Notification
        fields = ("id", "utilisateur", "utilisateur_id", "message", "type", "statut", "date_envoi")
        read_only_fields = ("id", "utilisateur", "date_envoi")
