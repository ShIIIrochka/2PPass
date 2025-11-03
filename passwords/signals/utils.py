# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group


def get_or_create_group(name: str) -> Group:
	"""Получить или создать Django-группу."""
	group, _ = Group.objects.get_or_create(name=name)
	return group
