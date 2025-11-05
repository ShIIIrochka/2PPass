# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PasswordGroup(models.Model):
	name = models.CharField(max_length=255, unique=True)
	description = models.TextField(blank=True, null=True)
	passwords = models.ManyToManyField(
		"passwords.Password",
		related_name="groups",
		blank=True,
	)
	members = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through="passwords.GroupMembership",
		related_name="password_groups",
		blank=True,
	)

	def __str__(self) -> str:
		return str(self.name)

	def get_role_for_user(self, user):
		membership = (
			self.memberships.filter(user=user).select_related("role").first()
		)
		return membership.role if membership else None

	class Meta:
		verbose_name = _("password storage")
		verbose_name_plural = _("Password Storages")
