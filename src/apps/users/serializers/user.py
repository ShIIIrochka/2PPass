from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import serializers

from apps.users.constants import UserRole

User = get_user_model()


class VaultAccessInputSerializer(serializers.Serializer):
    vault_id = serializers.IntegerField()
    access_level = serializers.ChoiceField(choices=['view', 'edit', 'admin'])


def _get_assignable_vault_ids(request_user):
    from apps.vaults.models import Vault

    if request_user.role == UserRole.ADMIN:
        return set(Vault.objects.filter(is_deleted=False).values_list('id', flat=True))

    from django.db.models import Q

    vault_ids = Vault.objects.filter(
        is_deleted=False
    ).filter(
        Q(created_by=request_user) | Q(access_list__user=request_user, access_list__access_level='admin')
    ).distinct().values_list('id', flat=True)

    return set(vault_ids)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'phone',
            'role',
            'custom_role',
            'is_active',
            'date_joined',
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    temporary_password = serializers.CharField(read_only=True)
    vault_accesses = VaultAccessInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'phone',
            'role',
            'custom_role',
            'password',
            'temporary_password',
            'vault_accesses',
        ]

    def validate_role(self, value):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        from apps.roles.utils.permissions import has_permission
        can_create_users = request.user.role in (UserRole.ADMIN, UserRole.MANAGER) or has_permission(request.user, 'users', 'create')
        if not can_create_users:
            raise serializers.ValidationError('Недостаточно прав для создания пользователя.')

        if request.user.role != UserRole.ADMIN and value != UserRole.EMPLOYEE:
            raise serializers.ValidationError('Недостаточно прав для назначения этой роли.')

        if request.user.role == UserRole.MANAGER and value != UserRole.EMPLOYEE:
            raise serializers.ValidationError('Менеджер может создавать только сотрудников.')
        return value

    def validate_custom_role(self, value):
        request = self.context.get('request')
        if value is None:
            return value
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        if request.user.role != UserRole.ADMIN:
            raise serializers.ValidationError('Только администратор может назначать кастомные роли.')
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.roles.models import CustomRole
        self.fields['custom_role'] = serializers.PrimaryKeyRelatedField(
            queryset=CustomRole.objects.all(),
            required=False,
            allow_null=True,
        )

    def create(self, validated_data):
        vault_accesses = validated_data.pop('vault_accesses', None)
        password = validated_data.pop('password', None)
        if not password:
            password = get_random_string(12)
            self._temporary_password = password
        
        email = validated_data.pop('email')
        request = self.context.get('request')

        with transaction.atomic():
            user = User.objects.create_user(email=email, password=password, **validated_data)
            user.password_changed = False
            user.save(update_fields=['password_changed'])

            if vault_accesses and request is not None:
                assignable_vault_ids = _get_assignable_vault_ids(request.user)
                access_by_vault = {int(item['vault_id']): item['access_level'] for item in vault_accesses}

                from apps.vaults.models import VaultAccess
                access_objects = []
                for vault_id, access_level in access_by_vault.items():
                    if vault_id not in assignable_vault_ids:
                        raise serializers.ValidationError({'vault_accesses': 'Недостаточно прав для назначения доступа к выбранному хранилищу.'})
                    access_objects.append(VaultAccess(
                        vault_id=vault_id,
                        user=user,
                        access_level=access_level,
                        granted_by=request.user,
                    ))

                if access_objects:
                    VaultAccess.objects.bulk_create(access_objects)

        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        temporary_password = getattr(self, '_temporary_password', None)
        if temporary_password:
            data['temporary_password'] = temporary_password
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Пароли не совпадают.'})
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']


class UserDetailSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    vault_accesses = serializers.SerializerMethodField()
    custom_role = serializers.IntegerField(source='custom_role_id', read_only=True)
    custom_role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'phone',
            'role',
            'custom_role',
            'custom_role_name',
            'is_active',
            'date_joined',
            'groups',
            'vault_accesses',
        ]
    
    def get_groups(self, obj):
        return [{'id': g.id, 'name': g.name} for g in obj.groups.all()]
    
    def get_vault_accesses(self, obj):
        from apps.vaults.models import VaultAccess
        accesses = VaultAccess.objects.filter(user=obj).select_related('vault', 'granted_by')
        return [
            {
                'vault_id': acc.vault.id,
                'vault_name': acc.vault.name,
                'access_level': acc.access_level,
                'granted_at': acc.granted_at,
                'granted_by': acc.granted_by.email if acc.granted_by else None,
            }
            for acc in accesses
        ]

    def get_custom_role_name(self, obj):
        if not obj.custom_role_id:
            return None
        return obj.custom_role.name


class UserUpdateSerializer(serializers.ModelSerializer):
    vault_accesses = VaultAccessInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'role',
            'custom_role',
            'is_active',
            'groups',
            'vault_accesses',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import Group
        from apps.roles.models import CustomRole
        self.fields['groups'] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=Group.objects.all(),
            required=False,
            allow_empty=True
        )
        self.fields['custom_role'] = serializers.PrimaryKeyRelatedField(
            queryset=CustomRole.objects.all(),
            required=False,
            allow_null=True,
        )
    
    def validate_role(self, value):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        
        from apps.roles.utils.permissions import has_permission
        can_edit_users = request.user.role in (UserRole.ADMIN, UserRole.MANAGER) or has_permission(request.user, 'users', 'edit')
        if not can_edit_users:
            raise serializers.ValidationError('Недостаточно прав для изменения пользователя.')

        if request.user.role != UserRole.ADMIN and value != UserRole.EMPLOYEE:
            raise serializers.ValidationError('Недостаточно прав для назначения этой роли.')

        if request.user.role == UserRole.MANAGER and value != UserRole.EMPLOYEE:
            raise serializers.ValidationError('Менеджер может изменять роль только на "Сотрудник".')
        
        return value
    
    def validate_email(self, value):
        instance = self.instance
        if instance and User.objects.filter(email=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def validate_custom_role(self, value):
        request = self.context.get('request')
        if value is None:
            return value
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        if request.user.role != UserRole.ADMIN:
            raise serializers.ValidationError('Только администратор может назначать кастомные роли.')
        return value
    
    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)
        vault_accesses = validated_data.pop('vault_accesses', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if groups is not None:
            instance.groups.set(groups)

        if vault_accesses is not None:
            request = self.context.get('request')
            if request is None:
                raise serializers.ValidationError({'vault_accesses': 'Невозможно обновить доступы к хранилищам.'})

            assignable_vault_ids = _get_assignable_vault_ids(request.user)
            access_by_vault = {int(item['vault_id']): item['access_level'] for item in vault_accesses}

            from apps.vaults.models import VaultAccess
            with transaction.atomic():
                VaultAccess.objects.filter(user=instance, vault_id__in=assignable_vault_ids).delete()

                access_objects = []
                for vault_id, access_level in access_by_vault.items():
                    if vault_id not in assignable_vault_ids:
                        raise serializers.ValidationError({'vault_accesses': 'Недостаточно прав для назначения доступа к выбранному хранилищу.'})
                    access_objects.append(VaultAccess(
                        vault_id=vault_id,
                        user=instance,
                        access_level=access_level,
                        granted_by=request.user,
                    ))

                if access_objects:
                    VaultAccess.objects.bulk_create(access_objects)
        
        return instance
