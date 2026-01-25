from django.contrib.auth.models import AnonymousUser
from .models import User


class MongoUserAdapter:
    def __init__(self, user):
        self._user = user
    
    def __getattr__(self, name):
        return getattr(self._user, name)
    
    @property
    def pk(self):
        return str(self._user.id)
    
    @property
    def id(self):
        return str(self._user.id)
    
    def save(self):
        self._user.save()
        return self
    
    def delete(self):
        self._user.delete()
    
    def __str__(self):
        return str(self._user)
