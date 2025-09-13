from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


class Utilisateur(models.Model):
    ROLES=[
        ('demandeur', 'Demandeur'),
        ('admin', 'Administrateur'),
        ('agent','Agent ASDM'),
    ]
    
    id= models.AutoField(primary_key=True)
    nom= models.CharField(max_length=100)
    prenom= models.CharField(max_length=100)
    email= models.EmailField(unique=True)
    mot_de_passe= models.CharField(max_length=128)
    role= models.CharField(max_length=20, choices=ROLES, default='demandeur')
    date_creation= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.role}"

    def set_password(self, raw_password):
        self.mot_de_passe=make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.mot_de_passe)

    def se_connecter(self):
        return True

    def modifier_profil(self):
        pass

    def consulter_notifications(self):
        return self.notifications.all()

    def creer_compte(self):
        return True

    @property
    def username(self):
        return self.email
    @property
    def first_name(self):
        return self.prenom
    @property
    def last_name(self):
        return self.nom
    
   
    @property
    def date_joined(self):
            return self.date_creation


class AgentASDM(models.Model):
   
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='agent_profile')
    droits_validation = models.BooleanField(default=False)
    fonction = models.CharField(max_length=100, blank=True)
    departement = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Agent {self.utilisateur.prenom} {self.utilisateur.nom} - {self.departement}"
    
    # Propriétés pour accéder aux attributs de l'utilisateur
    @property
    def id(self):
        return self.utilisateur.id
    
    @property
    def nom(self):
        return self.utilisateur.nom
    
    @property
    def prenom(self):
        return self.utilisateur.prenom
    
    @property
    def email(self):
        return self.utilisateur.email
    
    @property
    def role(self):
        return self.utilisateur.role
    
    @property
    def date_creation(self):
        return self.utilisateur.date_creation
    
    def valider_demande(self, demande):
        """Valide une demande de subvention"""
        demande.statut = 'accepte'
        demande.date_traitement = timezone.now()
        demande.agent_traitant = self
        demande.save()
        return True
    
    def rejeter_demande(self, demande):
        """Rejette une demande de subvention"""
        demande.statut = 'refuse'
        demande.date_traitement = timezone.now()
        demande.agent_traitant = self
        demande.save()
        return True
    
    def generer_rapport(self):
        """Génère un rapport"""
        return Rapport.objects.create(
            agent=self,
            date_generation=timezone.now()
        )
    
    def administrer_dossiers(self):
        """Administre les dossiers"""
        return DemandeSubvention.objects.all()


class DemandeSubvention(models.Model):
   
    TYPES = [
        ('formation', 'Formation'),
        ('equipement', 'Equipement'),
        ('soutien', 'Soutien financier'),
    ]
    
    STATUTS = [
        ('en_attente', 'En attente'),
        ('en_etude', 'En cours d\'étude'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]
    
    # Attributs du diagramme UML
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50, choices=TYPES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    commentaires = models.TextField(blank=True)
    
    # Relations
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='demandes_subvention')
    agent_traitant = models.ForeignKey(AgentASDM, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_traitees')
    
    def __str__(self):
        return f"Demande {self.id} - {self.utilisateur.prenom} {self.utilisateur.nom} - {self.montant}€"
    
    def soumettre(self):
        """Soumet la demande de subvention"""
        self.statut = 'en_attente'
        self.date_soumission = timezone.now()
        self.save()
        return True
    
    def modifier(self):
        """Modifie la demande de subvention"""
        return True
    
    def consulter_statut(self):
        """Consulte le statut de la demande"""
        return self.statut
    
    def ajouter_document(self, document):
        """Ajoute un document à la demande"""
        document.demande_subvention = self
        document.save()
        return True

class Paiement(models.Model):
    """
    Représente un paiement associé à une demande de subvention
    Correspond exactement au diagramme UML
    """
    MODES_PAIEMENT = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
    ]
    
    STATUTS = [
        ('en_attente', 'En attente'),
        ('traite', 'Traité'),
        ('echec', 'Échec'),
        ('annule', 'Annulé'),
    ]
    
    # Attributs du diagramme UML
    id = models.AutoField(primary_key=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField(null=True, blank=True)
    mode_paiement = models.CharField(max_length=20, choices=MODES_PAIEMENT)
    reference = models.CharField(max_length=100, unique=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    
    # Relation avec DemandeSubvention (1:1)
    demande_subvention = models.OneToOneField(DemandeSubvention, on_delete=models.CASCADE, related_name='paiement')
    
    def __str__(self):
        return f"Paiement {self.reference} - {self.montant}€"
    
    def traiter(self):
        """Traite le paiement"""
        self.statut = 'traite'
        self.date_paiement = timezone.now()
        self.save()
        return True
    
    def verifier(self):
        """Vérifie le paiement"""
        return True
    
    def annuler(self):
        """Annule le paiement"""
        self.statut = 'annule'
        self.save()
        return True

class Document(models.Model):
    """
    Représente un document attaché à une demande de subvention
    Correspond exactement au diagramme UML
    """
    TYPES = [
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('excel', 'Excel'),
        ('word', 'Word'),
        ('autre', 'Autre'),
    ]
    
    # Attributs du diagramme UML
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPES)
    chemin_fichier = models.FileField(upload_to='documents/')
    date_upload = models.DateTimeField(auto_now_add=True)
    taille_fichier = models.BigIntegerField()
    
    # Relation avec DemandeSubvention (N:1)
    demande_subvention = models.ForeignKey(DemandeSubvention, on_delete=models.CASCADE, related_name='documents')
    
    def __str__(self):
        return f"Document {self.nom} - {self.demande_subvention.id}"
    
    def uploader(self):
        """Upload le document"""
        return True
    
    def telecharger(self):
        """Télécharge le document"""
        return self.chemin_fichier.read()
    
    def supprimer(self):
        """Supprime le document"""
        self.delete()
        return True
    
    def valider(self):
        """Valide le document"""
        return True


class Rapport(models.Model):
    """
    Représente un rapport généré par le système
    Correspond exactement au diagramme UML
    """
    FORMATS = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ]
    
    # Attributs du diagramme UML
    id = models.AutoField(primary_key=True)
    periode = models.CharField(max_length=100)
    date_generation = models.DateTimeField(auto_now_add=True)
    statistiques = models.TextField(blank=True)
    format = models.CharField(max_length=20, choices=FORMATS, default='pdf')
    contenu = models.TextField(blank=True)
    
    # Relation avec AgentASDM (N:1)
    agent = models.ForeignKey(AgentASDM, on_delete=models.CASCADE, related_name='rapports')
    
    def __str__(self):
        return f"Rapport {self.id} - {self.periode}"
    
    def generer(self):
        """Génère le rapport"""
        return True
    
    def exporter(self):
        """Exporte le rapport"""
        return True
    
    def planifier(self):
        """Planifie la génération du rapport"""
        return True


class Notification(models.Model):
    """
    Représente une notification envoyée dans le système
    Correspond exactement au diagramme UML
    """
    TYPES = [
        ('alert', 'Alerte'),
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
    ]
    
    PRIORITES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    
    # Attributs du diagramme UML
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=TYPES)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    priorite = models.CharField(max_length=20, choices=PRIORITES, default='normale')
    
    # Relation avec Utilisateur (N:1)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    
    def __str__(self):
        return f"Notification {self.id} - {self.utilisateur.prenom} {self.utilisateur.nom}"
    
    def envoyer(self):
        """Envoie la notification"""
        return True
    
    def marquer_lu(self):
        """Marque la notification comme lue"""
        self.lu = True
        self.save()
        return True
    
    def supprimer(self):
        """Supprime la notification"""
        self.delete()
        return True
















# from django.db import models
# from django.contrib.auth.models import AbstractUser
# # Create your models here.
# class CustomUser(AbstractUser):
#     ROLES=[
#         ('demandeur', "Demandeur"),
#         ('admin','Administrateur'),
#         ('agent','Agent ASDM'),   
#     ]
    
#     email= models.EmailField(unique=True)
#     phone=models.CharField(max_length=20, blank=True)
#     role= models.CharField(max_length=20, choices=ROLES, default='demandeur')
#     USERNAME_FIELD='email'
#     REQUIRED_FIELDS=['username']
#     def __str__(self):
#         return f"{self.username} - {self.role}"
    

# class DossierDemande(models.Model):
#     type=[
#         ('formation', 'Formation'),
#         ('equipement', 'Equipement'),
#         ('soutien', 'Soutien fiancier'),
        
#     ]
#     Statut= [
#         ('en_attente', 'En attente'),
#         ('en_etude', 'En cours d\'etude'),
#         ('accepte', 'Accepté'),
#         ('refuse', 'Refusé'),
        
#     ]    
    
#     utilisateur= models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     type_subvention= models.CharField(max_length=50, choices=type)
#     montant_demande= models.DecimalField(max_digits=10, decimal_places=2)
#     description_projet= models.TextField()
#     fichiers= models.FileField(upload_to='dossiers/', blank=True, null=True)
#     date_depot= models.DateTimeField(auto_now_add=True)
#     statut= models.CharField(max_length=20, choices=Statut, default='en_attente')
    
#     def __str__(self):
#         return f"Dossier  {self.id} - {self.utilisateur.username} "
    
    
# class SuiviDossier(models.Model):
#     dossier= models.ForeignKey(DossierDemande, on_delete=models.CASCADE)
#     date_update = models.DateTimeField(auto_now_add=True)
#     commentaire = models.TextField()
#     statut= models.CharField(max_length=20, choices=DossierDemande.Statut, default='en_attente') 
    
#     def __str__(self):
#         return f"Suivi Dossier {self.dossier.id}"



# class Notification (models.Model):
#     Types =[
#         ('email', 'Email'),
#         ('sms', 'SMS'),
#         ('in_app', 'Notification in-app'),
        
#     ]
#     utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)   
#     message= models.TextField()
#     type= models.CharField(max_length=20, choices=Types)
#     statut= models.BooleanField(default= False)
#     date_envoi= models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"Notification {self.id} à {self.utilisateur.username}"
    