# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from passwords.admin.password.actions import log_access
from passwords.admin.password.display import (
	copy_button,
	groups_list,
	masked_password,
)
from passwords.admin.password.permissions import (
	can_add_password,
	can_change_password,
	can_delete_password,
	can_view_password,
)
from passwords.admin.password.views import reveal_view
from passwords.forms.password_admin import PasswordAdminForm
from passwords.models.password import Password


@admin.register(Password)
class PasswordAdmin(admin.ModelAdmin):
	form = PasswordAdminForm
	list_display = ("title", "url", "groups_list")
	exclude = ("password",)
	search_fields = ("title", "url")
	readonly_fields = ("masked_password", "copy_button")

	groups_list = groups_list
	masked_password = masked_password
	copy_button = copy_button

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
		return reveal_view(request, object_id)

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
