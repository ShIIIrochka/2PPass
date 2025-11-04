# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from passwords.models.password_group import GroupMembership


class GroupMembershipInline(admin.TabularInline):
	"""Встраиваемая таблица для отображения участий пользователя в группе паролей."""

	model = GroupMembership
	extra = 0
	raw_id_fields = ("user",)
	show_change_link = True

	verbose_name = _("Участник группы")
	verbose_name_plural = _("Участники группы")

	ordering = ("user__username",)

	def get_queryset(self, request):
		"""Возвращает queryset с подгруженными связанными записями пользователей."""
		qs = super().get_queryset(request)
		try:
			return qs.select_related("user")
		except Exception:
			return qs
