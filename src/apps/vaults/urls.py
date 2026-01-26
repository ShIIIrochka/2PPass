from django.urls import path

from apps.vaults.views import (
    vaults_list_view,
    vaults_create_view,
    vaults_users_view,
    vault_passwords_view,
    create_password_view,
    update_password_view,
    delete_password_view,
    trash_passwords_view,
    restore_password_view,
)

app_name = 'vaults'

urlpatterns = [
    path('', vaults_list_view, name='vaults-list'),
    path('create/', vaults_create_view, name='vaults-create'),
    path('users/', vaults_users_view, name='vaults-users'),
    path('<int:vault_id>/passwords/', vault_passwords_view, name='vault-passwords'),
    path('<int:vault_id>/passwords/create/', create_password_view, name='create-password'),
    path('<int:vault_id>/passwords/<int:password_id>/', update_password_view, name='update-password'),
    path('<int:vault_id>/passwords/<int:password_id>/delete/', delete_password_view, name='delete-password'),
    path('trash/', trash_passwords_view, name='trash-passwords'),
    path('trash/<int:password_id>/restore/', restore_password_view, name='restore-password'),
]
