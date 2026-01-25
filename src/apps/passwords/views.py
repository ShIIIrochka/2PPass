from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.passwords.utils.password_generator import generate_password
from apps.passwords.models import PasswordEntry
from apps.vaults.models import Vault, VaultAccess
from apps.audit.utils import log_action


class PasswordGeneratorPageView(LoginRequiredMixin, TemplateView):
    template_name = 'passwords/generator.html'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_password_view(request):
    try:
        length = int(request.data.get('length', 16))
        use_uppercase = request.data.get('use_uppercase', True)
        use_lowercase = request.data.get('use_lowercase', True)
        use_digits = request.data.get('use_digits', True)
        use_special = request.data.get('use_special', True)
        exclude_chars = request.data.get('exclude_chars', '')
    except (ValueError, TypeError):
        return Response(
            {'error': 'Неверные параметры генерации.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if length < 1 or length > 128:
        return Response(
            {'error': 'Длина пароля должна быть от 1 до 128 символов.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        password = generate_password(
            length=length,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_digits=use_digits,
            use_special=use_special,
            exclude_chars=exclude_chars,
        )
        return Response({'password': password})
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_accessible_vaults_view(request):
    user = request.user
    
    vaults = Vault.objects.filter(
        is_deleted=False
    ).filter(
        models.Q(created_by=user) | models.Q(accesses=user)
    ).distinct()
    
    vault_list = []
    for vault in vaults:
        access_level = None
        if vault.created_by == user:
            access_level = 'admin'
        else:
            try:
                access = VaultAccess.objects.get(vault=vault, user=user)
                access_level = access.access_level
            except VaultAccess.DoesNotExist:
                continue
        
        if access_level in ('admin', 'edit'):
            vault_list.append({
                'id': vault.id,
                'name': vault.name,
                'description': vault.description,
                'access_level': access_level,
            })
    
    return Response({'vaults': vault_list})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_password_to_vault_view(request):
    try:
        vault_id = int(request.data.get('vault_id'))
        title = request.data.get('title', '').strip()
        login = request.data.get('login', '').strip()
        password = request.data.get('password', '').strip()
        url = request.data.get('url', '').strip()
        notes = request.data.get('notes', '').strip()
    except (ValueError, TypeError):
        return Response(
            {'error': 'Неверные параметры.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    
    try:
        vault = Vault.objects.get(id=vault_id, is_deleted=False)
    except Vault.DoesNotExist:
        return Response(
            {'error': 'Хранилище не найдено.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    user = request.user
    
    can_edit = False
    if vault.created_by == user:
        can_edit = True
    else:
        try:
            access = VaultAccess.objects.get(vault=vault, user=user)
            if access.access_level in ('admin', 'edit'):
                can_edit = True
        except VaultAccess.DoesNotExist:
            pass
    
    if not can_edit:
        return Response(
            {'error': 'Недостаточно прав для добавления пароля в это хранилище.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    password_entry = PasswordEntry.objects.create(
        vault=vault,
        title=title,
        login=login,
        password=password,
        url=url if url else '',
        notes=notes if notes else '',
        created_by=user,
    )
    
    log_action(
        user=user,
        action='password_created_from_generator',
        resource_type='password',
        resource_id=password_entry.id,
        details={
            'vault_id': vault.id,
            'vault_name': vault.name,
            'title': title,
            'login': login,
        },
        request=request,
    )
    
    return Response({
        'id': password_entry.id,
        'title': password_entry.title,
        'vault_name': vault.name,
        'message': 'Пароль успешно сохранен в хранилище.',
    })
