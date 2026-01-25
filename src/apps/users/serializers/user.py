from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework import serializers

from apps.users.constants import UserRole

User = get_user_model()


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
            'is_active',
            'date_joined',
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    temporary_password = serializers.CharField(read_only=True)

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
            'password',
            'temporary_password',
        ]

    def validate_role(self, value):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        if request.user.role == UserRole.MANAGER and value != UserRole.EMPLOYEE:
            raise serializers.ValidationError('Менеджер может создавать только сотрудников.')
        if request.user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise serializers.ValidationError('Недостаточно прав для создания пользователя.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            password = get_random_string(12)
            self._temporary_password = password
        
        email = validated_data.pop('email')
        user = User.objects.create_user(email=email, password=password, **validated_data)
        user.password_changed = False
        user.save(update_fields=['password_changed'])
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


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'role',
            'is_active',
            'groups',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import Group
        self.fields['groups'] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=Group.objects.all(),
            required=False,
            allow_empty=True
        )
    
    def validate_role(self, value):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        
        if request.user.role == UserRole.MANAGER and value != UserRole.EMPLOYEE:
            raise serializers.ValidationError('Менеджер может изменять роль только на "Сотрудник".')
        
        if request.user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise serializers.ValidationError('Недостаточно прав для изменения пользователя.')
        
        return value
    
    def validate_email(self, value):
        instance = self.instance
        if instance and User.objects.filter(email=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value
    
    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if groups is not None:
            instance.groups.set(groups)
        
        return instance
