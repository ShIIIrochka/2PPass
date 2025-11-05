# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from passwords.models.group_membership import GroupMembership


class UserGroupMembershipInline(admin.TabularInline):
	model = GroupMembership
	fk_name = "user"
	extra = 0
	readonly_fields = ("group", "role", "created_at")
	can_delete = False
	verbose_name = _("Password group")
	verbose_name_plural = _("Password groups")
