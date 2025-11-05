# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from passwords.admin.users.admin import UserAdmin


from django.contrib.auth.models import Group

from passwords.admin.user import user_admin_site
from passwords.admin.passwords.admin import PasswordAdmin
from passwords.admin.trash.admin import TrashAdmin
from passwords.admin.groups.admin import PasswordGroupAdmin

from passwords.models.access_log import AccessLog
from passwords.models.password import Password, PasswordInTrash
from passwords.models.group_membership import GroupMembership
from passwords.models.storage import PasswordGroup
from passwords.models.tag import Tag
from passwords.models.role import Role
from passwords.admin.roles.admin import RoleAdmin


admin.site.site_header = '2PPass'
admin.site.site_title = '2PPass'
admin.site.index_title = _('Home')

User = get_user_model()
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(GroupMembership)
admin.site.register(AccessLog)
admin.site.register(PasswordInTrash, TrashAdmin)
admin.site.register(PasswordGroup, PasswordGroupAdmin)
admin.site.register(Password, PasswordAdmin)
admin.site.register(Tag)
# admin.site.unregister(Group)

user_admin_site.register(Password, PasswordAdmin)
user_admin_site.register(Tag)
user_admin_site.register(PasswordGroup, PasswordGroupAdmin)
