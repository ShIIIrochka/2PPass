from django.db import models


class Permission(models.Model):
    resource = models.CharField(max_length=100)
    actions = models.JSONField(default=list)
    role = models.ForeignKey('CustomRole', on_delete=models.CASCADE, related_name='permissions_list')
    
    class Meta:
        db_table = 'permissions'


class CustomRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'custom_roles'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_system']),
        ]
    
    def __str__(self):
        return self.name
