# -*- coding: utf-8 -*-

from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UserAdminAuthenticationForm(AdminAuthenticationForm):
	"""Форма аутентификации для пользовательской админки.
	Разрешён вход только для активных пользователей."""

	def confirm_login_allowed(self, user):
		if not getattr(user, "is_active", False):
			raise ValidationError(
				_("Учетная запись не активна."), code="inactive"
			)


class UserAdminSite(AdminSite):
	"""Админ-сайт для обычных пользователей."""

	site_header = _("2PPass — Корпоративный менеджер паролей")
	site_title = _("2PPass")
	index_title = _("Главная")
	login_form = UserAdminAuthenticationForm

	def has_permission(self, request):
		user = getattr(request, "user", None)
		return bool(
			user
			and getattr(user, "is_authenticated", False)
			and getattr(user, "is_active", False)
		)


user_admin_site = UserAdminSite(name="user_admin")
