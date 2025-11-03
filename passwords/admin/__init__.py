# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.admin import AdminSite

from passwords.admin.user import user_admin_site
from passwords.admin.passwords.admin import PasswordAdmin
from passwords.admin.groups.admin import PasswordGroupAdmin
from passwords.models.access_log import AccessLog
from passwords.models.password import Password
from passwords.models.password import PasswordInTrash
from passwords.admin.trash.admin import TrashAdmin
from passwords.models.password_group import GroupMembership, PasswordGroup

admin.site.site_header = 'Password Manager'
admin.site.site_title = 'Password Manager'
admin.site.index_title = 'Home'

admin.site.register(GroupMembership)
admin.site.register(AccessLog)
admin.site.register(PasswordInTrash, TrashAdmin)
admin.site.register(Password, PasswordAdmin)
user_admin_site.register(Password, PasswordAdmin)
user_admin_site.register(PasswordGroup, PasswordGroupAdmin)
