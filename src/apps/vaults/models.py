from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class VaultAccess(models.Model):
    ACCESS_LEVEL_CHOICES = [
        ('view', 'Просмотр'),
        ('edit', 'Редактирование'),
        ('admin', 'Администратор'),
    ]
    
    vault = models.ForeignKey('Vault', on_delete=models.CASCADE, related_name='access_list')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vault_accesses')
    access_level = models.CharField(max_length=10, choices=ACCESS_LEVEL_CHOICES)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_accesses')
    
    class Meta:
        db_table = 'vault_accesses'
        unique_together = [['vault', 'user']]


class Vault(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_vaults')
    tags = models.JSONField(default=list, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    accesses = models.ManyToManyField(User, through='VaultAccess', through_fields=('vault', 'user'), related_name='accessible_vaults')
    
    class Meta:
        db_table = 'vaults'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return self.name


