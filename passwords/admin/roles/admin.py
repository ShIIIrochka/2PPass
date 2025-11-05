# -*- coding: utf-8 -*-

from django.contrib import admin

from passwords.models.password_group import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ("name", "description")
	search_fields = ("name", "description")
	filter_horizontal = ("permissions",)
	ordering = ("name",)
