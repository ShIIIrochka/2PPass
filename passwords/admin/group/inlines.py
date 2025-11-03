# -*- coding: utf-8 -*-

from django.contrib import admin

from passwords.models.password_group import GroupMembership


class GroupMembershipInline(admin.TabularInline):
	model = GroupMembership
	extra = 0
	raw_id_fields = ("user",)
