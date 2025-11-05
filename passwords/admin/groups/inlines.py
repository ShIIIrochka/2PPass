# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from passwords.models.group_membership import GroupMembership


class GroupMembershipInline(admin.TabularInline):
	model = GroupMembership
	extra = 0
	autocomplete_fields = ("user", "role")
	show_change_link = True
	verbose_name = _("Member")
	verbose_name_plural = _("Members")
