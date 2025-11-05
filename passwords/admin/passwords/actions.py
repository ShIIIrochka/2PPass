# -*- coding: utf-8 -*-

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from passwords.models.access_log import AccessLog
from passwords.models.password import Password
from passwords.utils.client_id_getter import get_client_ip


ACTION_MAP = {
	"create": AccessLog.ACTION_CREATE,
	"change": AccessLog.ACTION_CHANGE,
	"delete": AccessLog.ACTION_DELETE,
	"view_page": AccessLog.ACTION_VIEW_PAGE,
	"reveal": AccessLog.ACTION_REVEAL,
}


def _resolve_password(
	obj_or_id: Password | int | str,
) -> Password | None:
	"""Получение объекта Password по экземпляру или по PK."""
	if isinstance(obj_or_id, Password):
		return obj_or_id
	return get_object_or_404(Password, pk=obj_or_id)


def log_access(
	request: HttpRequest, obj_or_id: Password | int | str, action: str
):
	"""Создание записи AccessLog."""
	try:
		password = _resolve_password(obj_or_id)
		action_code = ACTION_MAP.get(action, action)

		ip = ""
		try:
			ip = get_client_ip(request) or ""
		except Exception:
			ip = ""

		user_agent = ""
		try:
			user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]
		except Exception:
			user_agent = ""

		AccessLog.objects.create(
			user=getattr(request, "user", None),
			password=password,
			action=action_code,
			ip_address=ip,
			user_agent=user_agent,
		)
	except Exception:
		return None
