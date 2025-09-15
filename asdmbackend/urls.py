
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
admin.site.site_header = "ASDM - Administration"
admin.site.site_title = "ASDM Admin"
admin.site.index_title = "Panneau d'administration ASDM"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app_principale.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

