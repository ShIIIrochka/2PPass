# -*- coding: utf-8 -*-

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from passwords.models.role import Role
from passwords.models.storage import PasswordGroup


class GroupMembership(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="group_memberships",
	)
	group = models.ForeignKey(
		PasswordGroup,
		on_delete=models.CASCADE,
		related_name="memberships",
	)
	role = models.ForeignKey(
		Role,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		verbose_name=_("Role"),
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("user", "group")
		verbose_name = _("storage member")
		verbose_name_plural = _("Storage members")

	def can_read(self) -> bool:
		"""Проверка разрешений роли на чтение."""
		if not self.role:
			return False
		return self.role.permissions.filter(
			codename__in=["view_password"]
		).exists()

	def can_write(self) -> bool:
		"""Проверка разрешений роли на запись."""
		if not self.role:
			return False
		return self.role.permissions.filter(
			codename__in=["change_password", "add_password"]
		).exists()

	def get_role_display(self) -> str:
		return self.role.name if self.role else _("No role")

	def __str__(self) -> str:
		try:
			user_str = str(self.user)
		except Exception:
			user_str = f"user_id={self.user_id}"
		return f"{user_str} @ {self.group.name} ({self.role or _('No role')})"
