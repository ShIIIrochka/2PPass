# -*- coding: utf-8 -*-

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from passwords.admin.password.permissions import can_view_password
from passwords.models.access_log import AccessLog
from passwords.models.password import Password
from passwords.utils.client_id_getter import get_client_ip
from passwords.utils.crypto import decrypt_password


def reveal_view(request, object_id):
	if request.method != "POST":
		return JsonResponse({"error": "Only POST allowed"}, status=405)

	obj = get_object_or_404(Password, pk=object_id)

	if not (can_view_password(request.user, obj) or request.user.is_superuser):
		return JsonResponse({"error": "Permission denied"}, status=403)

	AccessLog.objects.create(
		user=request.user,
		password=obj,
		action=AccessLog.ACTION_REVEAL,
		ip_address=get_client_ip(request),
		user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
	)

	try:
		clear = decrypt_password(obj.password)
	except Exception:
		clear = "[decryption failed]"

	return JsonResponse({"password": clear})
