from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.passwords.urls import api_urlpatterns as passwords_api_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.web_urls')),
    path('passwords/', include('apps.passwords.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/vaults/', include('apps.vaults.urls')),
    path('api/passwords/', include((passwords_api_urls, 'passwords'), namespace='passwords_api')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/roles/', include('apps.roles.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
