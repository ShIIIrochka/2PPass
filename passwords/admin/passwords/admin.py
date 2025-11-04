# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _

from passwords.admin.passwords.actions import log_access
from passwords.admin.passwords.display import (
	copy_button,
	groups_list,
	masked_password,
)
from passwords.admin.passwords.permissions import (
	can_add_password,
	can_change_password,
	can_delete_password,
	can_view_password,
)
from passwords.admin.passwords.views import reveal_view as _reveal_view
from passwords.forms.password_admin import PasswordAdminForm
from passwords.models.password import Password


class PasswordAdmin(admin.ModelAdmin):
	"""Админка для модели Password."""

	form = PasswordAdminForm
	list_display = ("title", "url", "groups_list")
	exclude = ("password",)
	search_fields = ("title", "url")
	ordering = ("title",)

	groups_list = groups_list
	masked_password = masked_password
	copy_button = copy_button

	actions = ["move_to_trash", "restore_from_trash", "delete_forever"]

	@admin.action(description=_("Переместить в корзину"))
	def move_to_trash(self, request, queryset):
		"""Пометить записи как удалённые (в корзине).s"""
		queryset.update(in_trash=True)

	@admin.action(description=_("Восстановить из корзины"))
	def restore_from_trash(self, request, queryset):
		"""Снять пометку корзины."""
		queryset.update(in_trash=False)

	@admin.action(description=_("Удалить навсегда"))
	def delete_forever(self, request, queryset):
		"""Удаляем связи с группами, затем сами записи."""
		for password in queryset:
			password.groups.clear()
			password.delete()

	def has_view_permission(self, request, obj=None):
		"""Проверка прав доступа на просмотр записи."""
		return can_view_password(request.user, obj)

	def has_change_permission(self, request, obj=None):
		"""Проверка прав доступа на изменение записи."""
		return can_change_password(request.user, obj)

	def has_add_permission(self, request):
		"""Проверка прав доступа на добавление записи."""
		return can_add_password(request.user)

	def has_delete_permission(self, request, obj=None):
		"""Проверка прав доступа на удаление записи."""
		return can_delete_password(request.user, obj)

	def get_queryset(self, request):
		"""Получение списка паролей, доступных пользователю."""
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(groups__members=request.user).distinct()

	def get_readonly_fields(self, request, obj=None):
		"""Получение списка полей, доступных только для чтения."""
		readonly = list(super().get_readonly_fields(request, obj))
		if obj:
			readonly += ["masked_password", "copy_button"]
		return readonly

	def get_urls(self):
		"""Получение списка URL-адресов для админ-панели."""
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
		"""Проверка прав на просмотр пароля."""
		return _reveal_view(request, object_id)

	def change_view(self, request, object_id, form_url="", extra_context=None):
		"""Логгирование просмотра пароля."""
		log_access(request, object_id, "view_page")
		return super().change_view(request, object_id, form_url, extra_context)

	def response_add(self, request, obj, post_url_continue=None):
		"""Логгирование создания пароля."""
		log_access(request, obj, "create")
		return super().response_add(request, obj, post_url_continue)

	def response_change(self, request, obj):
		"""Логгирование изменения пароля."""
		log_access(request, obj, "change")
		return super().response_change(request, obj)

	def delete_model(self, request, obj):
		"""Логгирование удаления пароля."""
		log_access(request, obj, "delete")
		return super().delete_model(request, obj)


__all__ = ("PasswordAdmin",)
