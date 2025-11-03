# -*- coding: utf-8 -*-

from django.contrib import admin

from passwords.admin.group.inlines import GroupMembershipInline
from passwords.models.password_group import PasswordGroup


@admin.register(PasswordGroup)
class PasswordGroupAdmin(admin.ModelAdmin):
	list_display = ("name", "description", "members_list")
	inlines = [GroupMembershipInline]
	filter_horizontal = ("passwords",)

	def members_list(self, obj):
		return ", ".join(
			[
				f"{m.user} ({m.get_role_display()})"
				for m in obj.memberships.all()
			]
		)

	members_list.short_description = "Members"
