from django.db import models
from django.contrib.auth import get_user_model
from apps.vaults.models import Vault

from apps.passwords.fields import EncryptedTextField

User = get_user_model()


class PasswordEntry(models.Model):
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='password_entries')
    title = models.CharField(max_length=200)
    login = models.CharField(max_length=200)
    password = EncryptedTextField()
    url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(max_length=2000, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_passwords')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_passwords')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'passwords'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['login']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.login})"


class PasswordVersion(models.Model):
    password_entry = models.ForeignKey(PasswordEntry, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=50)
    login = models.CharField(max_length=200)
    password = EncryptedTextField()
    url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_password_versions')
    
    class Meta:
        db_table = 'password_versions'
        indexes = [
            models.Index(fields=['version']),
            models.Index(fields=['created_at']),
        ]
