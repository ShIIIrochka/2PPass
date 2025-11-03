# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class AccessLog(models.Model):
	ACTION_VIEW_PAGE = "view"
	ACTION_REVEAL = "reveal"
	ACTION_CREATE = "create"
	ACTION_CHANGE = "change"
	ACTION_DELETE = "delete"

	ACTION_CHOICES = (
		(ACTION_VIEW_PAGE, "View page"),
		(ACTION_REVEAL, "Reveal password"),
		(ACTION_CREATE, "Create"),
		(ACTION_CHANGE, "Change"),
		(ACTION_DELETE, "Delete"),
	)

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING
	)
	password = models.ForeignKey(
		"passwords.Password",
		on_delete=models.CASCADE,
		related_name="access_logs",
	)
	action = models.CharField(max_length=16, choices=ACTION_CHOICES)
	timestamp = models.DateTimeField(auto_now_add=True)
	ip_address = models.GenericIPAddressField(blank=True, null=True)
	user_agent = models.TextField(blank=True, null=True)
	extra = models.TextField(blank=True, null=True)

	class Meta:
		ordering = ("-timestamp",)

	def __str__(self) -> str:
		return f"{self.timestamp} {self.user} {self.action} {self.password}"
