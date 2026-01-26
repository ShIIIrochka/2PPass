from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.roles.models import CustomRole, Permission
from apps.users.constants import UserRole
from apps.audit.utils import log_action

User = get_user_model()


class RolesPageView(LoginRequiredMixin, TemplateView):
    template_name = 'roles/roles.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != UserRole.ADMIN:
            from django.shortcuts import redirect
            return redirect('vaults_web:vaults_page')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        context['is_admin'] = self.request.user.role == UserRole.ADMIN
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def roles_list_view(request):
    if request.user.role != UserRole.ADMIN:
        return Response(
            {'error': 'Доступ запрещён. Только администраторы могут просматривать роли.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    standard_roles = [
        {'id': 'admin', 'name': 'Администратор', 'description': 'Полный доступ ко всем функциям системы', 'is_system': True},
        {'id': 'manager', 'name': 'Менеджер', 'description': 'Управление сотрудниками и хранилищами', 'is_system': True},
        {'id': 'employee', 'name': 'Сотрудник', 'description': 'Базовый доступ к хранилищам', 'is_system': True},
    ]
    
    custom_roles = CustomRole.objects.all().order_by('-created_at')
    custom_roles_list = []
    for role in custom_roles:
        permissions = Permission.objects.filter(role=role)
        permissions_list = []
        for perm in permissions:
            permissions_list.append({
                'resource': perm.resource,
                'actions': perm.actions,
            })
        
        custom_roles_list.append({
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'is_system': role.is_system,
            'permissions': permissions_list,
            'created_at': role.created_at,
        })
    
    return Response({
        'standard_roles': standard_roles,
        'custom_roles': custom_roles_list,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def roles_create_view(request):
    if request.user.role != UserRole.ADMIN:
        return Response(
            {'error': 'Доступ запрещён. Только администраторы могут создавать роли.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    name = request.data.get('name', '').strip()
    description = request.data.get('description', '').strip()
    permissions = request.data.get('permissions', [])
    
    if not name:
        return Response(
            {'error': 'Название роли обязательно.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if CustomRole.objects.filter(name=name).exists():
        return Response(
            {'error': 'Роль с таким названием уже существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(permissions, list):
        return Response(
            {'error': 'Разрешения должны быть списком.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    with transaction.atomic():
        role = CustomRole.objects.create(
            name=name,
            description=description,
            is_system=False,
        )
        
        permission_objects = []
        for perm_data in permissions:
            resource = perm_data.get('resource', '').strip()
            actions = perm_data.get('actions', [])
            
            if resource and isinstance(actions, list):
                permission_objects.append(Permission(
                    role=role,
                    resource=resource,
                    actions=actions,
                ))
        
        if permission_objects:
            Permission.objects.bulk_create(permission_objects)
    
    log_action(
        user=request.user,
        action='custom_role_created',
        resource_type='role',
        resource_id=role.id,
        details={
            'name': role.name,
            'permissions_count': len(permission_objects),
        },
        request=request,
    )
    
    permissions_list = []
    for perm in role.permissions_list.all():
        permissions_list.append({
            'resource': perm.resource,
            'actions': perm.actions,
        })
    
    return Response({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'is_system': role.is_system,
        'permissions': permissions_list,
        'message': 'Роль успешно создана.',
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def roles_detail_view(request, role_id):
    if request.user.role != UserRole.ADMIN:
        return Response(
            {'error': 'Доступ запрещён. Только администраторы могут просматривать роли.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        role = CustomRole.objects.get(id=role_id)
    except CustomRole.DoesNotExist:
        return Response(
            {'error': 'Роль не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    permissions = Permission.objects.filter(role=role)
    permissions_list = []
    for perm in permissions:
        permissions_list.append({
            'resource': perm.resource,
            'actions': perm.actions,
        })
    
    return Response({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'is_system': role.is_system,
        'permissions': permissions_list,
        'created_at': role.created_at,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_resources_view(request):
    if request.user.role != UserRole.ADMIN:
        return Response(
            {'error': 'Доступ запрещён.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    resources = [
        {
            'id': 'vaults',
            'name': 'Хранилища',
            'actions': ['view', 'create', 'edit', 'delete', 'admin'],
        },
        {
            'id': 'passwords',
            'name': 'Пароли',
            'actions': ['view', 'create', 'edit', 'delete'],
        },
        {
            'id': 'users',
            'name': 'Пользователи',
            'actions': ['view', 'create', 'edit', 'delete'],
        },
        {
            'id': 'audit',
            'name': 'Аудит',
            'actions': ['view', 'export'],
        },
    ]
    
    return Response({'resources': resources})
