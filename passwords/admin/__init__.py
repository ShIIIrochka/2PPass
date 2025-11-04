# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from passwords.admin.user import user_admin_site
from passwords.admin.passwords.admin import PasswordAdmin
from passwords.admin.groups.admin import PasswordGroupAdmin
from passwords.admin.trash.admin import TrashAdmin

from passwords.models.access_log import AccessLog
from passwords.models.password import Password, PasswordInTrash
from passwords.models.password_group import GroupMembership, PasswordGroup
from passwords.models.tag import Tag

admin.site.site_header = _('2PPass — Corporate Password Manager')
admin.site.site_title = _('2PPass')
admin.site.index_title = _('Home')

admin.site.register(GroupMembership)
admin.site.register(AccessLog)
admin.site.register(PasswordInTrash, TrashAdmin)
admin.site.register(PasswordGroup, PasswordGroupAdmin)
admin.site.register(Password, PasswordAdmin)
admin.site.register(Tag)

user_admin_site.register(Password, PasswordAdmin)
user_admin_site.register(Tag)
user_admin_site.register(PasswordGroup, PasswordGroupAdmin)
