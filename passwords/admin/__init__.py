# -*- coding: utf-8 -*-

from django.contrib import admin

from passwords.admin.base import user_admin_site
from passwords.admin.password.password import PasswordAdmin
from passwords.admin.group.password_group import PasswordGroupAdmin
from passwords.models.access_log import AccessLog
from passwords.models.password import Password
from passwords.models.password_group import GroupMembership, PasswordGroup

admin.site.register(GroupMembership)
admin.site.register(AccessLog)
user_admin_site.register(Password, PasswordAdmin)
user_admin_site.register(PasswordGroup, PasswordGroupAdmin)
