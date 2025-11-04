# -*- coding: utf-8 -*-
#
from typing import Any

from django.contrib import admin
from django.urls import path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from passwords.admin.passwords.actions import log_access
from passwords.admin.passwords.display import copy_button
from passwords.admin.passwords.permissions import (
	can_add_password,
	can_change_password,
	can_delete_password,
	can_view_password,
)
from passwords.admin.passwords.views import reveal_view as _reveal_view
from passwords.forms.password_admin import PasswordAdminForm


class PasswordAdmin(admin.ModelAdmin):
	"""Админка для модели Password."""

	form = PasswordAdminForm
	list_display = ("title", "url", "get_groups", "get_tags")
	exclude = ("password", "in_trash")
	search_fields = ("title", "url", "tags")
	ordering = ("title",)
	copy_button = copy_button

	actions = ["move_to_trash", "restore_from_trash", "delete_forever"]

	@admin.action(description=_("Trash"))
	def move_to_trash(self, request, queryset):
		"""Пометить записи как удалённые (в корзине)."""
		queryset.update(in_trash=True)

	@admin.action(description=_("Restore from trash"))
	def restore_from_trash(self, request, queryset):
		"""Снять пометку корзины."""
		queryset.update(in_trash=False)

	@admin.action(description=_("Delete forever"))
	def delete_forever(self, request, queryset):
		"""Удалить записи навсегда, предварительно очистив связи."""
		for password in queryset:
			password.groups.clear()
			password.delete()

	def get_groups(self, obj: Any) -> str:
		"""Возвращает список имён групп."""
		return ", ".join(g.name for g in obj.groups.all())

	get_groups.short_description = _("Groups")

	def masked_password(self, obj: Any) -> str:
		"""Возвращает скрытое представление пароля."""
		return "••••••••"

	masked_password.short_description = _("Password (masked)")

	def get_tags(self, obj: Any) -> str:
		"""Возвращает список тегов."""
		return ", ".join(t.name for t in obj.tags.all())

	get_tags.short_description = _("Tags")

	def has_view_permission(self, request, obj=None):
		return can_view_password(request.user, obj)

	def has_change_permission(self, request, obj=None):
		return can_change_password(request.user, obj)

	def has_add_permission(self, request):
		return can_add_password(request.user)

	def has_delete_permission(self, request, obj=None):
		return can_delete_password(request.user, obj)

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(groups__members=request.user).distinct()

	def get_readonly_fields(self, request, obj=None):
		readonly = list(super().get_readonly_fields(request, obj))
		if obj:
			readonly += ["masked_password", "copy_button"]
		return readonly

	def get_urls(self):
		urls = super().get_urls()
		custom = [
			path(
				"<path:object_id>/reveal/",
				self.admin_site.admin_view(self.reveal_view),
				name="passwords_password_reveal",
			),
		]
		return custom + urls

	@method_decorator(csrf_protect)
	def reveal_view(self, request, object_id):
		"""Проверяет права и возвращает расшифрованный пароль."""
		return _reveal_view(request, object_id)

	def change_view(self, request, object_id, form_url="", extra_context=None):
		log_access(request, object_id, "view_page")
		return super().change_view(request, object_id, form_url, extra_context)

	def response_add(self, request, obj, post_url_continue=None):
		log_access(request, obj, "create")
		return super().response_add(request, obj, post_url_continue)

	def response_change(self, request, obj):
		log_access(request, obj, "change")
		return super().response_change(request, obj)

	def delete_model(self, request, obj):
		log_access(request, obj, "delete")
		return super().delete_model(request, obj)
