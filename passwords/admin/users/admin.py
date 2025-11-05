# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from passwords.admin.users.inlines import UserGroupMembershipInline


class UserAdmin(BaseUserAdmin):
	"""Админка для пользователей с отображением групп паролей."""

	inlines = [UserGroupMembershipInline]
