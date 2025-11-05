# -*- coding: utf-8 -*-

from django.contrib.auth.models import Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
	"""Роль для участников групп паролей."""

	name = models.CharField(_("Name"), max_length=100, unique=True)
	description = models.TextField(_("Description"), blank=True)
	permissions = models.ManyToManyField(
		Permission,
		blank=True,
		related_name="password_roles",
		verbose_name=_("Permissions"),
	)

	class Meta:
		verbose_name = _("Role")
		verbose_name_plural = _("Roles")
		ordering = ("name",)

	def __str__(self):
		return self.name
