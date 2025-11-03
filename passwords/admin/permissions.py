# -*- coding: utf-8 -*-

from passwords.models.password_group import GroupMembership


def can_restore_password(user, trash_obj) -> bool:
    if user.is_superuser:
        return True
    if not getattr(trash_obj, "groups_snapshot", None):
        return False
    group_ids = [g["id"] for g in trash_obj.groups_snapshot]
    return GroupMembership.objects.filter(
        user=user,
        group_id__in=group_ids,
        role=GroupMembership.ROLE_READ_WRITE,
    ).exists()


def can_read_password(user, password_obj) -> bool:
    if user.is_superuser:
        return True
    return GroupMembership.objects.filter(
        user=user,
        group__passwords=password_obj,
        role__in=(GroupMembership.ROLE_READ, GroupMembership.ROLE_READ_WRITE)
    ).exists()


def can_write_password(user, password_obj) -> bool:
    if user.is_superuser:
        return True
    return GroupMembership.objects.filter(
        user=user,
        group__passwords=password_obj,
        role=GroupMembership.ROLE_READ_WRITE,
    ).exists()
