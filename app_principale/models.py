from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class CustomUser(AbstractUser):
    ROLES=[
        ('demandeur', "Demandeur"),
        ('admin','Administrateur'),
        ('agent','Agent ASDM'),   
    ]
    
    email= models.EmailField(unique=True)
    phone=models.CharField(max_length=20, blank=True)
    role= models.CharField(max_length=20, choices=ROLES, default='demandeur')
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['username']
    def __str__(self):
        return f"{self.username} - {self.role}"
    

class DossierDemande(models.Model):
    type=[
        ('formation', 'Formation'),
        ('equipement', 'Equipement'),
        ('soutien', 'Soutien fiancier'),
        
    ]
    Statut= [
        ('en_attente', 'En attente'),
        ('en_etude', 'En cours d\'etude'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
        
    ]    
    
    utilisateur= models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type_subvention= models.CharField(max_length=50, choices=type)
    montant_demande= models.DecimalField(max_digits=10, decimal_places=2)
    description_projet= models.TextField()
    fichiers= models.FileField(upload_to='dossiers/', blank=True, null=True)
    date_depot= models.DateTimeField(auto_now_add=True)
    statut= models.CharField(max_length=20, choices=Statut, default='en_attente')
    
    def __str__(self):
        return f"Dossier  {self.id} - {self.utilisateur.username} "
    
    
class SuiviDossier(models.Model):
    dossier= models.ForeignKey(DossierDemande, on_delete=models.CASCADE)
    date_update = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField()
    statut= models.CharField(max_length=20, choices=DossierDemande.Statut, default='en_attente') 
    
    def __str__(self):
        return f"Suivi Dossier {self.dossier.id}"



class Notification (models.Model):
    Types =[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'Notification in-app'),
        
    ]
    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)   
    message= models.TextField()
    type= models.CharField(max_length=20, choices=Types)
    statut= models.BooleanField(default= False)
    date_envoi= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification {self.id} à {self.utilisateur.username}"
    