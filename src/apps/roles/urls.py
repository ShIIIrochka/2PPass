from django.urls import path

from apps.roles.views import (
    roles_list_view,
    roles_create_view,
    roles_detail_view,
    available_resources_view,
)

app_name = 'roles'

urlpatterns = [
    path('', roles_list_view, name='roles-list'),
    path('create/', roles_create_view, name='roles-create'),
    path('<int:role_id>/', roles_detail_view, name='roles-detail'),
    path('resources/', available_resources_view, name='available-resources'),
]
