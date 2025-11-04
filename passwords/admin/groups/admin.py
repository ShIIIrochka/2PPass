# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from passwords.admin.groups.inlines import GroupMembershipInline
from passwords.models.password_group import PasswordGroup


class PasswordGroupAdmin(admin.ModelAdmin):
	"""Админка для групп паролей."""

	list_display = ("name", "description", "members_list")
	search_fields = ("name", "description")
	ordering = ("name",)
	inlines = [GroupMembershipInline]
	filter_horizontal = ("passwords",)

	def members_list(self, obj):
		"""Возвращает список участников группы в формате "user (роль)"."""
		return ", ".join(
			f"{m.user} ({m.get_role_display()})" for m in obj.memberships.all()
		)

	members_list.short_description = _("Участники")
	members_list.admin_order_field = None
