from django.urls import path

from apps.users.views import (
    UsersPageView,
    LoginPageView,
    PasswordChangePageView,
)

app_name = 'users_web'

urlpatterns = [
    path('', LoginPageView.as_view(), name='login'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('password-change/', PasswordChangePageView.as_view(), name='password_change'),
    path('users/', UsersPageView.as_view(), name='users_page'),
]
