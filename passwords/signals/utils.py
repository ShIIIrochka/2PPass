# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from passwords.models.password import Password


def get_or_create_group(name: str) -> Group:
	"""Получить или создать Django-группу с нужными permissions."""
	group, created = Group.objects.get_or_create(name=name)

	if created:
		if name == "Password Viewers":
			perms = ["view_password"]
		elif name == "Password Editors":
			perms = [
				"view_password",
				"add_password",
				"change_password",
				"delete_password",
			]
		else:
			perms = []

		if perms:
			content_type = ContentType.objects.get_for_model(Password)
			permissions = Permission.objects.filter(
				content_type=content_type, codename__in=perms
			)
			group.permissions.set(permissions)

	return group
