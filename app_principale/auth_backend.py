from django.contrib.auth.backends import BaseBackend
from .models import Utilisateur

class UtilisateurAhthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None,**kwargs):
        try:
            utilisateur=Utilisateur.objects.get(email=email)
            if utilisateur.check_password(password):
                return utilisateur
        except Utilisateur.DoesNotExist:
            return None
        return None    
                   
    def get_user(self, user_id):
        try:
            return Utilisateur.objects.get(pk=user_id)
        except Utilisateur.DoesNotExist:
            return None     