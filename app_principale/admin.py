from django.contrib import admin
from .models import CustomUser, DossierDemande, SuiviDossier, Notification

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "role", "is_active", "date_joined", "last_login")
    list_filter = ("role", "is_active", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)

@admin.register(DossierDemande)
class DossierDemandeAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "type_subvention", "montant_demande", "statut", "date_depot")
    list_filter = ("type_subvention", "statut", "date_depot")
    search_fields = ("description_projet", "utilisateur__email")
    date_hierarchy = "date_depot"

@admin.register(SuiviDossier)
class SuiviDossierAdmin(admin.ModelAdmin):
    list_display = ("id", "dossier", "statut", "date_update")
    list_filter = ("statut", "date_update")
    search_fields = ("commentaire",)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "type", "statut", "date_envoi")
    list_filter = ("type", "statut", "date_envoi")
    search_fields = ("message",)
