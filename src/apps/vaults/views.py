from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models, transaction
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.audit.utils import log_action
from apps.users.constants import UserRole
from apps.users.permissions import IsAdminOrManager
from apps.vaults.models import Vault, VaultAccess, VaultGroupAccess
from apps.passwords.models import PasswordEntry
from django.utils import timezone

User = get_user_model()

_ACCESS_RANK = {'view': 0, 'edit': 1, 'admin': 2}


def _max_access_level(levels):
    if not levels:
        return None
    return max(levels, key=lambda lvl: _ACCESS_RANK.get(lvl, -1))


class VaultsPageView(LoginRequiredMixin, TemplateView):
    template_name = 'vaults/vaults_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.roles.utils.permissions import has_permission
        context['user_role'] = self.request.user.role
        context['is_admin'] = self.request.user.role == UserRole.ADMIN
        context['is_manager'] = self.request.user.role == UserRole.MANAGER
        context['can_create'] = context['is_admin'] or context['is_manager'] or has_permission(self.request.user, 'vaults', 'create')
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vaults_list_view(request):
    user = request.user
    
    if user.role == UserRole.ADMIN:
        vaults = Vault.objects.filter(is_deleted=False)
    else:
        vaults = Vault.objects.filter(
            is_deleted=False
        ).filter(
            models.Q(created_by=user)
            | models.Q(accesses=user)
            | models.Q(group_access_list__group__in=user.groups.all())
        ).distinct()

    vault_list = []
    for vault in vaults:
        if vault.created_by == user:
            access_level = 'admin'
        else:
            levels = []
            direct_level = VaultAccess.objects.filter(vault=vault, user=user).values_list('access_level', flat=True).first()
            if direct_level:
                levels.append(direct_level)

            group_levels = VaultGroupAccess.objects.filter(
                vault=vault,
                group__in=user.groups.all(),
            ).values_list('access_level', flat=True)
            levels.extend(list(group_levels))

            access_level = _max_access_level(levels) or 'view'

        vault_list.append({
            'id': vault.id,
            'name': vault.name,
            'description': vault.description,
            'tags': vault.tags,
            'created_by': vault.created_by.email,
            'access_level': access_level,
            'users_count': vault.access_list.count() + vault.group_access_list.count(),
            'created_at': vault.created_at,
        })

    return Response({'vaults': vault_list})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vaults_create_view(request):
    from apps.roles.utils.permissions import has_permission
    if request.user.role not in (UserRole.ADMIN, UserRole.MANAGER) and not has_permission(request.user, 'vaults', 'create'):
        return Response(
            {'error': 'Недостаточно прав.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        name = request.data.get('name', '').strip()
        description = request.data.get('description', '').strip()
        tags = request.data.get('tags', [])
        access_level = request.data.get('access_level', 'edit')
        users = request.data.get('users', [])
        groups = request.data.get('groups', [])
    except (TypeError, ValueError):
        return Response(
            {'error': 'Неверные параметры.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not name:
        return Response(
            {'error': 'Название хранилища обязательно.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if access_level not in ['view', 'edit', 'admin']:
        return Response(
            {'error': 'Неверный уровень доступа.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    tags_list = []
    if isinstance(tags, list):
        tags_list = [tag.strip() for tag in tags if str(tag).strip()]
    elif isinstance(tags, str):
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

    user_ids = []
    if isinstance(users, list):
        user_ids = [int(u) for u in users if str(u).isdigit()]
    elif isinstance(users, str):
        user_ids = [int(u.strip()) for u in users.split(',') if u.strip().isdigit()]

    target_users = User.objects.filter(id__in=user_ids, is_active=True)

    group_ids = []
    if isinstance(groups, list):
        group_ids = [int(g) for g in groups if str(g).isdigit()]
    elif isinstance(groups, str):
        group_ids = [int(g.strip()) for g in groups.split(',') if g.strip().isdigit()]

    from django.contrib.auth.models import Group
    target_groups = Group.objects.filter(id__in=group_ids).order_by('name')

    if request.user.role == UserRole.MANAGER:
        if target_users.exclude(role=UserRole.EMPLOYEE).exists():
            return Response(
                {'error': 'Менеджер может назначать только сотрудников.'},
                status=status.HTTP_403_FORBIDDEN
            )

    with transaction.atomic():
        vault = Vault.objects.create(
            name=name,
            description=description,
            tags=tags_list,
            created_by=request.user,
        )

        access_entries = []
        for user in target_users:
            if user == request.user:
                continue
            access_entries.append(VaultAccess(
                vault=vault,
                user=user,
                access_level=access_level,
                granted_by=request.user,
            ))

        if access_entries:
            VaultAccess.objects.bulk_create(access_entries)

        group_access_entries = []
        for group in target_groups:
            group_access_entries.append(VaultGroupAccess(
                vault=vault,
                group=group,
                access_level=access_level,
                granted_by=request.user,
            ))

        if group_access_entries:
            VaultGroupAccess.objects.bulk_create(group_access_entries)

    log_action(
        user=request.user,
        action='vault_created',
        resource_type='vault',
        resource_id=vault.id,
        details={
            'name': vault.name,
            'assigned_users': [u.id for u in target_users],
            'assigned_groups': [g.id for g in target_groups],
            'access_level': access_level,
            'tags': tags_list,
        },
        request=request,
    )

    return Response({
        'id': vault.id,
        'name': vault.name,
        'message': 'Хранилище успешно создано.',
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vaults_users_view(request):
    from apps.roles.utils.permissions import has_permission
    if request.user.role not in (UserRole.ADMIN, UserRole.MANAGER) and not has_permission(request.user, 'vaults', 'create'):
        return Response(
            {'error': 'Недостаточно прав.'},
            status=status.HTTP_403_FORBIDDEN
        )

    queryset = User.objects.filter(is_active=True)
    if request.user.role == UserRole.MANAGER:
        queryset = queryset.filter(role=UserRole.EMPLOYEE)

    users = []
    for user in queryset.order_by('email'):
        users.append({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        })

    return Response({'users': users})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vault_passwords_view(request, vault_id):
    try:
        vault = Vault.objects.get(id=vault_id, is_deleted=False)
    except Vault.DoesNotExist:
        return Response(
            {'error': 'Хранилище не найдено.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    user = request.user
    
    has_access, access_level, can_edit = _check_vault_access(user, vault)
    if not has_access:
        return Response(
            {'error': 'Нет доступа к этому хранилищу.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    passwords = PasswordEntry.objects.filter(
        vault=vault,
        is_deleted=False
    ).order_by('-created_at')
    
    password_list = []
    for pwd in passwords:
        password_list.append({
            'id': pwd.id,
            'title': pwd.title,
            'login': pwd.login,
            'password': pwd.password,
            'url': pwd.url,
            'notes': pwd.notes,
            'tags': pwd.tags,
            'created_at': pwd.created_at,
            'updated_at': pwd.updated_at,
            'created_by': pwd.created_by.email,
        })
    
    return Response({
        'vault': {
            'id': vault.id,
            'name': vault.name,
            'description': vault.description,
        },
        'passwords': password_list,
        'access_level': access_level,
        'can_edit': can_edit,
    })


def _check_vault_access(user, vault):
    if vault.created_by == user:
        return True, 'admin', True

    levels = []
    direct_level = VaultAccess.objects.filter(vault=vault, user=user).values_list('access_level', flat=True).first()
    if direct_level:
        levels.append(direct_level)

    group_levels = VaultGroupAccess.objects.filter(
        vault=vault,
        group__in=user.groups.all(),
    ).values_list('access_level', flat=True)
    levels.extend(list(group_levels))

    access_level = _max_access_level(levels)
    if not access_level:
        return False, None, False

    can_edit = access_level in ('admin', 'edit')
    return True, access_level, can_edit


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_password_view(request, vault_id, password_id):
    try:
        vault = Vault.objects.get(id=vault_id, is_deleted=False)
    except Vault.DoesNotExist:
        return Response(
            {'error': 'Хранилище не найдено.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        password_entry = PasswordEntry.objects.get(id=password_id, vault=vault, is_deleted=False)
    except PasswordEntry.DoesNotExist:
        return Response(
            {'error': 'Пароль не найден.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    has_access, access_level, can_edit = _check_vault_access(request.user, vault)
    
    if not has_access:
        return Response(
            {'error': 'Нет доступа к этому хранилищу.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not can_edit:
        return Response(
            {'error': 'Недостаточно прав для редактирования паролей в этом хранилище.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    old_password = password_entry.password
    old_data = {
        'title': password_entry.title,
        'login': password_entry.login,
        'url': password_entry.url,
        'notes': password_entry.notes,
        'tags': password_entry.tags,
    }
    
    title = request.data.get('title', '').strip()
    login = request.data.get('login', '').strip()
    password = request.data.get('password', '').strip()
    url = request.data.get('url', '').strip()
    notes = request.data.get('notes', '').strip()
    tags = request.data.get('tags', [])
    
    if not title:
        return Response(
            {'error': 'Название обязательно.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not login:
        return Response(
            {'error': 'Логин обязателен.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not password:
        return Response(
            {'error': 'Пароль обязателен.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    tags_list = []
    if isinstance(tags, list):
        tags_list = [tag.strip() for tag in tags if str(tag).strip()]
    elif isinstance(tags, str):
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    password_entry.title = title
    password_entry.login = login
    password_entry.password = password
    password_entry.url = url
    password_entry.notes = notes
    password_entry.tags = tags_list
    password_entry.updated_by = request.user
    password_entry.save()
    
    new_data = {
        'title': password_entry.title,
        'login': password_entry.login,
        'url': password_entry.url,
        'notes': password_entry.notes,
        'tags': password_entry.tags,
    }
    
    changes = {}
    for key in old_data:
        if old_data[key] != new_data[key]:
            changes[key] = {'old': old_data[key], 'new': new_data[key]}
    
    if old_password != password:
        changes['password'] = {'old': '***', 'new': '***'}
    
    log_action(
        user=request.user,
        action='password_updated',
        resource_type='password',
        resource_id=password_entry.id,
        details={
            'vault_id': vault.id,
            'vault_name': vault.name,
            'changes': changes,
        },
        request=request,
    )
    
    return Response({
        'id': password_entry.id,
        'message': 'Пароль успешно обновлен.',
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_password_view(request, vault_id, password_id):
    try:
        vault = Vault.objects.get(id=vault_id, is_deleted=False)
    except Vault.DoesNotExist:
        return Response(
            {'error': 'Хранилище не найдено.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        password_entry = PasswordEntry.objects.get(id=password_id, vault=vault, is_deleted=False)
    except PasswordEntry.DoesNotExist:
        return Response(
            {'error': 'Пароль не найден.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    has_access, access_level, can_edit = _check_vault_access(request.user, vault)
    
    if not has_access:
        return Response(
            {'error': 'Нет доступа к этому хранилищу.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not can_edit:
        return Response(
            {'error': 'Недостаточно прав для удаления паролей в этом хранилище.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    password_entry.is_deleted = True
    password_entry.deleted_at = timezone.now()
    password_entry.save()
    
    log_action(
        user=request.user,
        action='password_deleted',
        resource_type='password',
        resource_id=password_entry.id,
        details={
            'vault_id': vault.id,
            'vault_name': vault.name,
            'title': password_entry.title,
        },
        request=request,
    )
    
    return Response({
        'message': 'Пароль успешно удален.',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_password_view(request, vault_id):
    try:
        vault = Vault.objects.get(id=vault_id, is_deleted=False)
    except Vault.DoesNotExist:
        return Response(
            {'error': 'Хранилище не найдено.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    has_access, access_level, can_edit = _check_vault_access(request.user, vault)
    
    if not has_access:
        return Response(
            {'error': 'Нет доступа к этому хранилищу.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not can_edit:
        return Response(
            {'error': 'Недостаточно прав для добавления паролей в это хранилище.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    title = request.data.get('title', '').strip()
    login = request.data.get('login', '').strip()
    password = request.data.get('password', '').strip()
    url = request.data.get('url', '').strip()
    notes = request.data.get('notes', '').strip()
    tags = request.data.get('tags', [])
    
    if not title:
        return Response(
            {'error': 'Название обязательно.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not login:
        return Response(
            {'error': 'Логин обязателен.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not password:
        return Response(
            {'error': 'Пароль обязателен.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    tags_list = []
    if isinstance(tags, list):
        tags_list = [tag.strip() for tag in tags if str(tag).strip()]
    elif isinstance(tags, str):
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    password_entry = PasswordEntry.objects.create(
        vault=vault,
        title=title,
        login=login,
        password=password,
        url=url if url else '',
        notes=notes if notes else '',
        tags=tags_list,
        created_by=request.user,
    )
    
    log_action(
        user=request.user,
        action='password_created',
        resource_type='password',
        resource_id=password_entry.id,
        details={
            'vault_id': vault.id,
            'vault_name': vault.name,
            'title': password_entry.title,
            'login': password_entry.login,
        },
        request=request,
    )
    
    return Response({
        'id': password_entry.id,
        'message': 'Пароль успешно добавлен.',
    }, status=status.HTTP_201_CREATED)


class VaultPasswordsPageView(LoginRequiredMixin, TemplateView):
    template_name = 'vaults/vault_passwords.html'
    
    def dispatch(self, request, *args, **kwargs):
        vault_id = kwargs.get('vault_id')
        if not vault_id:
            from django.shortcuts import redirect
            return redirect('vaults_web:vaults_page')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vault_id = self.kwargs.get('vault_id')
        context['vault_id'] = int(vault_id) if vault_id else 0
        return context


class TrashPageView(LoginRequiredMixin, TemplateView):
    template_name = 'vaults/trash.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        context['is_admin'] = self.request.user.role == UserRole.ADMIN
        context['is_manager'] = self.request.user.role == UserRole.MANAGER
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trash_passwords_view(request):
    user = request.user
    
    vault_ids = []
    if user.role == UserRole.ADMIN:
        vaults = Vault.objects.filter(is_deleted=False)
        vault_ids = list(vaults.values_list('id', flat=True))
    else:
        vaults = Vault.objects.filter(
            is_deleted=False
        ).filter(
            models.Q(created_by=user)
            | models.Q(accesses=user)
            | models.Q(group_access_list__group__in=user.groups.all())
        ).distinct()
        vault_ids = list(vaults.values_list('id', flat=True))
    
    deleted_passwords = PasswordEntry.objects.filter(
        vault_id__in=vault_ids,
        is_deleted=True
    ).select_related('vault', 'created_by')
    
    vault_filter = request.query_params.get('vault_id')
    if vault_filter:
        try:
            vault_id = int(vault_filter)
            if vault_id in vault_ids:
                deleted_passwords = deleted_passwords.filter(vault_id=vault_id)
        except (ValueError, TypeError):
            pass
    
    date_from = request.query_params.get('date_from')
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            date_from_obj = timezone.make_aware(date_from_obj)
            deleted_passwords = deleted_passwords.filter(deleted_at__gte=date_from_obj)
        except (ValueError, TypeError):
            pass
    
    date_to = request.query_params.get('date_to')
    if date_to:
        try:
            from datetime import datetime, timedelta
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = timezone.make_aware(date_to_obj) + timedelta(days=1)
            deleted_passwords = deleted_passwords.filter(deleted_at__lt=date_to_obj)
        except (ValueError, TypeError):
            pass
    
    deleted_passwords = deleted_passwords.order_by('-deleted_at')
    
    password_list = []
    for pwd in deleted_passwords:
        has_access, access_level, _can_edit = _check_vault_access(user, pwd.vault)
        
        if has_access:
            password_list.append({
                'id': pwd.id,
                'title': pwd.title,
                'login': pwd.login,
                'password': pwd.password,
                'url': pwd.url,
                'notes': pwd.notes,
                'tags': pwd.tags,
                'vault_id': pwd.vault.id,
                'vault_name': pwd.vault.name,
                'deleted_at': pwd.deleted_at,
                'created_at': pwd.created_at,
                'created_by': pwd.created_by.email,
                'access_level': access_level,
            })
    
    available_vaults = []
    for vault in vaults:
        available_vaults.append({
            'id': vault.id,
            'name': vault.name,
        })
    
    return Response({
        'passwords': password_list,
        'vaults': available_vaults,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_password_view(request, password_id):
    if request.user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        return Response(
            {'error': 'Доступ запрещён. Только администраторы и менеджеры могут восстанавливать пароли.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        password_entry = PasswordEntry.objects.get(id=password_id, is_deleted=True)
    except PasswordEntry.DoesNotExist:
        return Response(
            {'error': 'Пароль не найден в корзине.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        vault = Vault.objects.get(id=password_entry.vault_id, is_deleted=False)
    except Vault.DoesNotExist:
        return Response(
            {'error': 'Хранилище не найдено.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    has_access, access_level, can_edit = _check_vault_access(request.user, vault)
    
    if not has_access:
        return Response(
            {'error': 'Нет доступа к этому хранилищу.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not can_edit:
        return Response(
            {'error': 'Недостаточно прав для восстановления паролей в этом хранилище.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    password_entry.is_deleted = False
    password_entry.deleted_at = None
    password_entry.save()
    
    log_action(
        user=request.user,
        action='password_restored',
        resource_type='password',
        resource_id=password_entry.id,
        details={
            'vault_id': vault.id,
            'vault_name': vault.name,
            'title': password_entry.title,
        },
        request=request,
    )
    
    return Response({
        'message': 'Пароль успешно восстановлен.',
    })
