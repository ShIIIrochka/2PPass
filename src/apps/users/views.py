from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.users.constants import UserRole
from apps.users.permissions import IsAdminOrManager
from apps.users.serializers import (
    UserCreateSerializer,
    UserListSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
)
from apps.audit.utils import log_action

User = get_user_model()


class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminOrManager]
    queryset = User.objects.all().order_by('id')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == UserRole.MANAGER:
            queryset = queryset.filter(role=UserRole.EMPLOYEE)
        
        role_filter = self.request.query_params.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        group_filter = self.request.query_params.get('group')
        if group_filter:
            queryset = queryset.filter(groups__id=group_filter).distinct()
        
        ordering = self.request.query_params.get('ordering', 'id')
        if ordering.lstrip('-') in ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']:
            queryset = queryset.order_by(ordering)
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserListSerializer
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        current_user = request.user
        
        if current_user.role == UserRole.MANAGER and instance.role != UserRole.EMPLOYEE:
            return Response(
                {'error': 'Менеджер может редактировать только сотрудников.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_data = {
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'phone': instance.phone,
            'role': instance.role,
            'is_active': instance.is_active,
            'groups': list(instance.groups.values_list('id', flat=True)),
        }
        
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            instance.refresh_from_db()
            new_data = {
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'phone': instance.phone,
                'role': instance.role,
                'is_active': instance.is_active,
                'groups': list(instance.groups.values_list('id', flat=True)),
            }
            
            changes = {}
            for key in old_data:
                if old_data[key] != new_data[key]:
                    changes[key] = {'old': old_data[key], 'new': new_data[key]}
            
            log_action(
                user=current_user,
                action='user_updated',
                resource_type='user',
                resource_id=instance.id,
                details={
                    'target_user_email': instance.email,
                    'changes': changes,
                },
                request=request,
            )
        
        return response


class UsersPageView(LoginRequiredMixin, TemplateView):
    template_name = 'users/users_page.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        
        if request.user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            return redirect('/login/')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        context['is_admin'] = self.request.user.role == UserRole.ADMIN
        context['is_manager'] = self.request.user.role == UserRole.MANAGER
        return context


class LoginPageView(TemplateView):
    template_name = 'users/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.password_changed:
                return redirect('password_change')
            return redirect('users_page')
        return super().dispatch(request, *args, **kwargs)


class PasswordChangePageView(LoginRequiredMixin, TemplateView):
    template_name = 'users/password_change.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.password_changed:
            return redirect('users_page')
        return super().dispatch(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Неверный email или пароль.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Учетная запись деактивирована.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not user.check_password(password):
        return Response(
            {'error': 'Неверный email или пароль.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    login(request, user)
    
    return Response({
        'id': user.id,
        'email': user.email,
        'password_changed': user.password_changed,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Выход выполнен успешно.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change_view(request):
    if request.user.password_changed:
        return Response(
            {'error': 'Пароль уже был изменен.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = PasswordChangeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    old_password = serializer.validated_data['old_password']
    
    if not user.check_password(old_password):
        return Response(
            {'old_password': 'Неверный текущий пароль.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    new_password = serializer.validated_data['new_password']
    user.set_password(new_password)
    user.password_changed = True
    user.save(update_fields=['password', 'password_changed'])
    
    return Response({'message': 'Пароль успешно изменен.'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    
    if request.method == 'GET':
        serializer = ProfileUpdateSerializer(user)
        return Response(serializer.data)
    
    if request.method == 'PATCH':
        if not user.password_changed:
            return Response(
                {'error': 'Сначала необходимо изменить пароль.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminOrManager])
def deactivate_user_view(request, user_id):
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    current_user = request.user
    
    if current_user.role == UserRole.MANAGER and target_user.role != UserRole.EMPLOYEE:
        return Response(
            {'error': 'Менеджер может отзывать доступ только у сотрудников.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if target_user.id == current_user.id:
        return Response(
            {'error': 'Нельзя отозвать доступ у самого себя.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    target_user.is_active = False
    target_user.save(update_fields=['is_active'])
    
    log_action(
        user=current_user,
        action='user_deactivated',
        resource_type='user',
        resource_id=target_user.id,
        details={
            'target_user_email': target_user.email,
            'target_user_role': target_user.role,
        },
        request=request,
    )
    
    return Response({'message': 'Доступ успешно отозван.'})


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def get_groups_view(request):
    groups = Group.objects.all().order_by('name')
    groups_list = [{'id': g.id, 'name': g.name} for g in groups]
    return Response({'groups': groups_list})


@api_view(['POST'])
@permission_classes([IsAdminOrManager])
def delete_user_view(request, user_id):
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    current_user = request.user
    
    if current_user.role == UserRole.MANAGER and target_user.role != UserRole.EMPLOYEE:
        return Response(
            {'error': 'Менеджер может удалять только сотрудников.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if target_user.id == current_user.id:
        return Response(
            {'error': 'Нельзя удалить самого себя.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    target_email = target_user.email
    target_role = target_user.role
    
    target_user.delete()
    
    log_action(
        user=current_user,
        action='user_deleted',
        resource_type='user',
        resource_id=user_id,
        details={
            'target_user_email': target_email,
            'target_user_role': target_role,
        },
        request=request,
    )
    
    return Response({'message': 'Пользователь успешно удален.'})
