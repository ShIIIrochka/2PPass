# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class TrashAdmin(admin.ModelAdmin):
	"""Админка для корзины паролей."""

	list_display = ("title", "url", "in_trash")
	search_fields = ("title", "url")
	actions = ["restore_from_trash", "delete_forever"]

	def get_queryset(self, request):
		"""Получение записей, помеченных как в корзине."""
		qs = super().get_queryset(request)
		return qs.filter(in_trash=True)

	@admin.action(description=_("Восстановить из корзины"))
	def restore_from_trash(self, request, queryset):
		"""Снимаем флаг корзины для выбранных записей."""
		queryset.update(in_trash=False)

	@admin.action(description=_("Удалить навсегда"))
	def delete_forever(self, request, queryset):
		"""Удаляем навсегда выбранные записи."""
		for password in queryset:
			password.groups.clear()
			password.delete()
