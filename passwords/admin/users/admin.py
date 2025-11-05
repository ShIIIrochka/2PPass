# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from passwords.admin.users.inlines import UserGroupMembershipInline


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	"""Админка для пользователей с отображением групп паролей."""

	inlines = [UserGroupMembershipInline]
