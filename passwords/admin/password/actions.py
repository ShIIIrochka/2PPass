# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404

from passwords.models.access_log import AccessLog
from passwords.models.password import Password
from passwords.utils.client_id_getter import get_client_ip


ACTION_MAP = {
	"create": AccessLog.ACTION_CREATE,
	"change": AccessLog.ACTION_CHANGE,
	"delete": AccessLog.ACTION_DELETE,
	"view_page": AccessLog.ACTION_VIEW_PAGE,
}


def log_access(request, obj_or_id, action):
	try:
		obj = (
			obj_or_id
			if isinstance(obj_or_id, Password)
			else get_object_or_404(Password, pk=obj_or_id)
		)
		AccessLog.objects.create(
			user=request.user,
			password=obj,
			action=ACTION_MAP.get(action, action),
			ip_address=get_client_ip(request),
			user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
		)
	except Exception:
		pass
