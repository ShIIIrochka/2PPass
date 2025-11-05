# -*- coding: utf-8 -*-

from passwords.models.group_membership import GroupMembership


def sync_user_django_groups(user):
	"""Пересчитывает Django-группы пользователя на основе членств в PasswordGroup."""

	memberships = user.group_memberships.select_related("role").all()

	has_write = any(m.can_write() for m in memberships)
	has_read = any(m.can_read() for m in memberships)

	if has_write:
		user.groups.add(group_rw)
	elif has_read:
		user.groups.add(group_read)
