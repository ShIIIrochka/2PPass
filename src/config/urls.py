from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from apps.passwords.urls import api_urlpatterns as passwords_api_urls
from apps.users.views import UsersPageView
from apps.audit.views import AuditPageView
from apps.roles.views import RolesPageView

@login_required
def home_view(request):
    if not request.user.password_changed:
        return redirect('users_web:password_change')
    return redirect('vaults_web:vaults_page')

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', include('apps.users.web_urls')),
    path('users/', UsersPageView.as_view(), name='users_page'),
    path('vaults/', include('apps.vaults.web_urls')),
    path('audit/', AuditPageView.as_view(), name='audit_page'),
    path('roles/', RolesPageView.as_view(), name='roles_page'),
    path('passwords/', include('apps.passwords.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/vaults/', include('apps.vaults.urls')),
    path('api/passwords/', include((passwords_api_urls, 'passwords'), namespace='passwords_api')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/roles/', include('apps.roles.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('admin/', admin.site.urls),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
