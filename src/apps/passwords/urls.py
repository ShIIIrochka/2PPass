from django.urls import path

from apps.passwords.views import (
    PasswordGeneratorPageView,
    generate_password_view,
    get_accessible_vaults_view,
    save_password_to_vault_view,
)

app_name = 'passwords'

urlpatterns = [
    path('generator/', PasswordGeneratorPageView.as_view(), name='generator'),
]

api_urlpatterns = [
    path('generate/', generate_password_view, name='generate'),
    path('vaults/', get_accessible_vaults_view, name='vaults'),
    path('save/', save_password_to_vault_view, name='save'),
]
