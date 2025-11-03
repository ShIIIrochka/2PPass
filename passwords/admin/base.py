# -*- coding: utf-8 -*-

from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


class UserAdminAuthenticationForm(AdminAuthenticationForm):
	def confirm_login_allowed(self, user):
		if not user.is_active:
			raise ValidationError(
				message="This account is inactive.", code="inactive"
			)


class UserAdminSite(AdminSite):
	site_header = "Passwords — User Console"
	login_form = UserAdminAuthenticationForm

	def has_permission(self, request):
		return request.user.is_authenticated and request.user.is_active


user_admin_site = UserAdminSite(name="user_admin")
