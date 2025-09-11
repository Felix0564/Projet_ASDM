from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, DossierDemandeViewSet, SuiviDossierViewSet, NotificationViewSet, api_home

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'dossiers', DossierDemandeViewSet, basename='dossiers')
router.register(r'suivis', SuiviDossierViewSet, basename='suivis')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', api_home, name='api_home'),  
    path('api/', include(router.urls)),   
]

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
