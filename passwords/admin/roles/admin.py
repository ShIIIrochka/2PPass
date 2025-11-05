# -*- coding: utf-8 -*-

from django.contrib import admin


class RoleAdmin(admin.ModelAdmin):
	list_display = ("name", "description")
	search_fields = ("name", "description")
	filter_horizontal = ("permissions",)
	ordering = ("name",)
