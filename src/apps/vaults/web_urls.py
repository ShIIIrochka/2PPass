from django.urls import path

from apps.vaults.views import VaultsPageView, VaultPasswordsPageView, TrashPageView

app_name = 'vaults_web'

urlpatterns = [
    path('', VaultsPageView.as_view(), name='vaults_page'),
    path('<int:vault_id>/', VaultPasswordsPageView.as_view(), name='vault_passwords_page'),
    path('trash/', TrashPageView.as_view(), name='trash_page'),
]
