# -*- coding: utf-8 -*-

from passwords.models.group_membership import GroupMembership


def can_view_password(user, obj=None):
	if user.is_superuser:
		return True
	if obj is None:
		return GroupMembership.objects.filter(user=user).exists()
	return GroupMembership.objects.filter(
		user=user,
		group__passwords=obj,
		role__in=(GroupMembership.ROLE_READ, GroupMembership.ROLE_READ_WRITE),
	).exists()


def can_change_password(user, obj=None):
	if user.is_superuser:
		return True
	if obj is None:
		return GroupMembership.objects.filter(
			user=user, role=GroupMembership.ROLE_READ_WRITE
		).exists()
	return GroupMembership.objects.filter(
		user=user,
		group__passwords=obj,
		role=GroupMembership.ROLE_READ_WRITE,
	).exists()


def can_add_password(user):
	return (
		user.is_superuser
		or GroupMembership.objects.filter(
			user=user, role=GroupMembership.ROLE_READ_WRITE
		).exists()
	)


def can_delete_password(user, obj=None):
	if user.is_superuser:
		return True
	if obj is None:
		return False
	return GroupMembership.objects.filter(
		user=user,
		group__passwords=obj,
		role=GroupMembership.ROLE_READ_WRITE,
	).exists()
