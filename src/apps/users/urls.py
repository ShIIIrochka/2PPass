from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    UserViewSet,
    login_view,
    logout_view,
    password_change_view,
    profile_view,
    get_groups_view,
    deactivate_user_view,
    delete_user_view,
)

app_name = 'users'

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-change/', password_change_view, name='password-change'),
    path('profile/', profile_view, name='profile'),
    path('groups/', get_groups_view, name='groups'),
    path('<int:user_id>/deactivate/', deactivate_user_view, name='deactivate-user'),
    path('<int:user_id>/delete/', delete_user_view, name='delete-user'),
    path('', include(router.urls)),  # Router в конец
]
