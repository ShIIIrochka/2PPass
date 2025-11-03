# -*- coding: utf-8 -*-

from passwords.models.password_group import GroupMembership
from passwords.signals.utils import get_or_create_group


def sync_user_django_groups(user):
	"""Пересчитывает Django-группы пользователя на основе членств в PasswordGroup."""
	group_read = get_or_create_group("Password Viewers")
	group_rw = get_or_create_group("Password Editors")

	user.groups.remove(group_read, group_rw)

	if user.group_memberships.filter(
		role=GroupMembership.ROLE_READ_WRITE
	).exists():
		print("fdfd")
		user.groups.add(group_rw)
	elif user.group_memberships.filter(role=GroupMembership.ROLE_READ).exists():
		print("---")
		user.groups.add(group_read)
