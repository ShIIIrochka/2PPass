# -*- coding: utf-8 -*-

from __future__ import annotations

from django.conf import settings
from django.db import models


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
		membership = self.memberships.filter(user=user).first()
		return membership.role if membership else None


class GroupMembership(models.Model):
	ROLE_READ = "R"
	ROLE_READ_WRITE = "RW"
	ROLE_CHOICES = (
		(ROLE_READ, "Read"),
		(ROLE_READ_WRITE, "Read & Write"),
	)

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
	role = models.CharField(
		max_length=3, choices=ROLE_CHOICES, default=ROLE_READ
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("user", "group")
		verbose_name = "Group membership"
		verbose_name_plural = "Group memberships"

	def can_read(self) -> bool:
		return self.role in (self.ROLE_READ, self.ROLE_READ_WRITE)

	def can_write(self) -> bool:
		return self.role == self.ROLE_READ_WRITE

	def __str__(self) -> str:
		try:
			user_str = str(self.user)
		except Exception:
			user_str = f"user_id={self.user_id}"
		return f"{user_str} @ {self.group.name} ({self.get_role_display()})"
