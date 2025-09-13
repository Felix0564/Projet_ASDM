from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UtilisateurViewSet, AgentASDMViewSet, DemandeSubventionViewSet,
    DocumentViewSet, PaiementViewSet, RapportViewSet, NotificationViewSet, 
    api_home, login_view, logout_view, user_profile
)

router = DefaultRouter()
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateurs')
router.register(r'agents', AgentASDMViewSet, basename='agents')
router.register(r'demandes', DemandeSubventionViewSet, basename='demandes')
router.register(r'documents', DocumentViewSet, basename='documents')
router.register(r'paiements', PaiementViewSet, basename='paiements')
router.register(r'rapports', RapportViewSet, basename='rapports')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    # Page d'accueil de l'API
    path('', api_home, name='api_home'),
    
    # Authentification
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/profile/', user_profile, name='user_profile'),
    
    # Endpoints de l'API
    path('api/', include(router.urls)),
    
    # Endpoints spécifiques pour les actions métier
    path('api/demandes/<int:pk>/valider/', 
         DemandeSubventionViewSet.as_view({'patch': 'update_statut'}), 
         name='valider_demande'),
    path('api/demandes/<int:pk>/rejeter/', 
         DemandeSubventionViewSet.as_view({'patch': 'update_statut'}), 
         name='rejeter_demande'),
    path('api/demandes/<int:pk>/documents/', 
         DemandeSubventionViewSet.as_view({'post': 'ajouter_document'}), 
         name='ajouter_document'),
    
    # Endpoints pour les agents
    path('api/agents/<int:pk>/valider-demande/', 
         AgentASDMViewSet.as_view({'post': 'valider_demande'}), 
         name='agent_valider_demande'),
    path('api/agents/<int:pk>/rejeter-demande/', 
         AgentASDMViewSet.as_view({'post': 'rejeter_demande'}), 
         name='agent_rejeter_demande'),
    
    # Endpoints pour les paiements
    path('api/paiements/<int:pk>/traiter/', 
         PaiementViewSet.as_view({'post': 'traiter_paiement'}), 
         name='traiter_paiement'),
    path('api/paiements/<int:pk>/annuler/', 
         PaiementViewSet.as_view({'post': 'annuler_paiement'}), 
         name='annuler_paiement'),
    
    # Endpoints pour les notifications
    path('api/notifications/<int:pk>/marquer-lu/', 
         NotificationViewSet.as_view({'post': 'marquer_lu'}), 
         name='marquer_notification_lu'),
]


#from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import UserViewSet, DossierDemandeViewSet, SuiviDossierViewSet, NotificationViewSet, api_home

# router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='users')
# router.register(r'dossiers', DossierDemandeViewSet, basename='dossiers')
# router.register(r'suivis', SuiviDossierViewSet, basename='suivis')
# router.register(r'notifications', NotificationViewSet, basename='notifications')

# urlpatterns = [
#     path('', api_home, name='api_home'),  
#     path('api/', include(router.urls)),   
# ]

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import UserViewSet, DossierDemandeViewSet, SuiviDossierViewSet, NotificationViewSet

# router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='users')
# router.register(r'dossiers', DossierDemandeViewSet, basename='dossiers')
# router.register(r'suivis', SuiviDossierViewSet, basename='suivis')
# router.register(r'notifications', NotificationViewSet, basename='notifications')

# urlpatterns = [
#     path('', include(router.urls)),
# ]
