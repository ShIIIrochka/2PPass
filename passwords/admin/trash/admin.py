# -*- coding: utf-8 -*-

from django.contrib import admin


class TrashAdmin(admin.ModelAdmin):
	list_display = ("title", "url", "in_trash")
	search_fields = ("title", "url")
	actions = ["restore_from_trash", "delete_forever"]

	# Показываем только те, что в корзине
	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.filter(in_trash=True)

	@admin.action(description="Восстановить из корзины")
	def restore_from_trash(self, request, queryset):
		queryset.update(in_trash=False)

	@admin.action(description="Удалить навсегда")
	def delete_forever(self, request, queryset):
		for password in queryset:
			password.groups.clear()
			password.delete()
