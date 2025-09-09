
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
admin.site.site_header = "ASDM - Administration"
admin.site.site_title = "ASDM Admin"
admin.site.index_title = "Panneau d'administration ASDM"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app_principale.urls')),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

