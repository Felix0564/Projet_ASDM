from django.contrib import admin
from .models import (
    Utilisateur, AgentASDM, DemandeSubvention, 
    Paiement, Document, Rapport, Notification
)

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "prenom", "nom", "role", "date_creation")
    list_filter = ("role", "date_creation")
    search_fields = ("email", "prenom", "nom")
    ordering = ("-date_creation",)
    readonly_fields = ("date_creation",)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'email')
        }),
        ('Authentification', {
            'fields': ('mot_de_passe',)
        }),
        ('Rôle et permissions', {
            'fields': ('role',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

@admin.register(AgentASDM)
class AgentASDMAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "fonction", "departement", "droits_validation")
    list_filter = ("droits_validation", "departement", "fonction")
    search_fields = ("utilisateur__email", "utilisateur__prenom", "utilisateur__nom", "fonction", "departement")
    ordering = ("-utilisateur__date_creation",)
    
    fieldsets = (
        ('Utilisateur associé', {
            'fields': ('utilisateur',)
        }),
        ('Informations professionnelles', {
            'fields': ('fonction', 'departement')
        }),
        ('Permissions', {
            'fields': ('droits_validation',)
        }),
    )

@admin.register(DemandeSubvention)
class DemandeSubventionAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "type", "montant", "statut", "date_soumission", "agent_traitant")
    list_filter = ("type", "statut", "date_soumission", "agent_traitant")
    search_fields = ("commentaires", "utilisateur__email", "utilisateur__prenom", "utilisateur__nom")
    date_hierarchy = "date_soumission"
    ordering = ("-date_soumission",)
    readonly_fields = ("date_soumission", "date_traitement")
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('utilisateur', 'type', 'montant', 'statut')
        }),
        ('Traitement', {
            'fields': ('agent_traitant', 'date_traitement', 'commentaires')
        }),
        ('Dates', {
            'fields': ('date_soumission',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("id", "demande_subvention", "montant", "mode_paiement", "statut", "date_paiement", "reference")
    list_filter = ("statut", "mode_paiement", "date_paiement")
    search_fields = ("reference", "demande_subvention__utilisateur__email")
    date_hierarchy = "date_paiement"
    ordering = ("-date_paiement",)
    readonly_fields = ("date_paiement",)
    
    fieldsets = (
        ('Informations de paiement', {
            'fields': ('demande_subvention', 'montant', 'mode_paiement', 'reference')
        }),
        ('Statut', {
            'fields': ('statut', 'date_paiement')
        }),
    )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "type", "demande_subvention", "date_upload", "taille_fichier")
    list_filter = ("type", "date_upload")
    search_fields = ("nom", "demande_subvention__utilisateur__email")
    date_hierarchy = "date_upload"
    ordering = ("-date_upload",)
    readonly_fields = ("date_upload", "taille_fichier")
    
    fieldsets = (
        ('Informations du document', {
            'fields': ('nom', 'type', 'chemin_fichier')
        }),
        ('Association', {
            'fields': ('demande_subvention',)
        }),
        ('Métadonnées', {
            'fields': ('date_upload', 'taille_fichier'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "periode", "format", "date_generation")
    list_filter = ("format", "date_generation", "agent__departement")
    search_fields = ("periode", "agent__utilisateur__email", "agent__utilisateur__prenom", "agent__utilisateur__nom")
    date_hierarchy = "date_generation"
    ordering = ("-date_generation",)
    readonly_fields = ("date_generation",)
    
    fieldsets = (
        ('Informations du rapport', {
            'fields': ('agent', 'periode', 'format')
        }),
        ('Contenu', {
            'fields': ('statistiques', 'contenu')
        }),
        ('Métadonnées', {
            'fields': ('date_generation',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "type", "priorite", "lu", "date_envoi")
    list_filter = ("type", "priorite", "lu", "date_envoi")
    search_fields = ("contenu", "utilisateur__email", "utilisateur__prenom", "utilisateur__nom")
    date_hierarchy = "date_envoi"
    ordering = ("-date_envoi",)
    readonly_fields = ("date_envoi",)
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('utilisateur',)
        }),
        ('Contenu', {
            'fields': ('type', 'priorite', 'contenu')
        }),
        ('Statut', {
            'fields': ('lu', 'date_envoi')
        }),
    )

# Configuration de l'interface d'administration
admin.site.site_header = "Administration ASDM"
admin.site.site_title = "ASDM Admin"
admin.site.index_title = "Gestion des subventions ASDM"

# from django.contrib import admin
# from .models import CustomUser, DossierDemande, SuiviDossier, Notification

# @admin.register(CustomUser)
# class CustomUserAdmin(admin.ModelAdmin):
#     list_display = ("id", "email", "username", "role", "is_active", "date_joined", "last_login")
#     list_filter = ("role", "is_active", "date_joined")
#     search_fields = ("email", "username", "first_name", "last_name", "phone")
#     ordering = ("-date_joined",)

# @admin.register(DossierDemande)
# class DossierDemandeAdmin(admin.ModelAdmin):
#     list_display = ("id", "utilisateur", "type_subvention", "montant_demande", "statut", "date_depot")
#     list_filter = ("type_subvention", "statut", "date_depot")
#     search_fields = ("description_projet", "utilisateur__email")
#     date_hierarchy = "date_depot"

# @admin.register(SuiviDossier)
# class SuiviDossierAdmin(admin.ModelAdmin):
#     list_display = ("id", "dossier", "statut", "date_update")
#     list_filter = ("statut", "date_update")
#     search_fields = ("commentaire",)

# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ("id", "utilisateur", "type", "statut", "date_envoi")
#     list_filter = ("type", "statut", "date_envoi")
#     search_fields = ("message",)
