# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_protect

from passwords.admin.forms import PasswordAdminForm
from passwords.models.access_log import AccessLog
from passwords.models.password import Password
from passwords.models.password_group import GroupMembership, PasswordGroup
from passwords.utils.client_id_getter import get_client_ip
from passwords.utils.crypto import decrypt_password


class UserAdminAuthenticationForm(AdminAuthenticationForm):
	def confirm_login_allowed(self, user):
		from django.core.exceptions import ValidationError

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


def user_can_read_password(user, password_obj) -> bool:
	if user.is_superuser:
		return True
	return GroupMembership.objects.filter(
		user=user,
		group__passwords=password_obj,
		role__in=(GroupMembership.ROLE_READ, GroupMembership.ROLE_READ_WRITE),
	).exists()


def user_can_write_password(user, password_obj) -> bool:
	if user.is_superuser:
		return True
	return GroupMembership.objects.filter(
		user=user,
		group__passwords=password_obj,
		role=GroupMembership.ROLE_READ_WRITE,
	).exists()


@admin.register(Password)
class PasswordAdmin(admin.ModelAdmin):
	form = PasswordAdminForm
	list_display = ("title", "url", "groups_list")
	exclude = ("password",)
	search_fields = ("title", "url")
	readonly_fields = ("masked_password", "copy_button")

	def groups_list(self, obj):
		return ", ".join([g.name for g in obj.groups.all()])

	groups_list.short_description = "Groups"

	def masked_password(self, obj):
		return "••••••••"

	masked_password.short_description = "Password (masked)"

	def copy_button(self, obj):
		from icecream import ic

		ic("Adsad")
		return format_html(
			"""
            <button type="button" class="button" onclick="copyPassword{0}()">Скопировать пароль</button>
            <script>
            function copyPassword{0}() {{
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                fetch('/admin/passwords/password/{0}/reveal/', {{
                    method: 'POST',
                    headers: {{ 'X-CSRFToken': csrftoken }},
                }})
                .then(resp => resp.json())
                .then(data => {{
                    if (data.password) {{
                        const textarea = document.createElement('textarea');
                        textarea.value = data.password;
                        document.body.appendChild(textarea);
                        textarea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textarea);
                        alert('Пароль скопирован в буфер обмена!');
                    }} else {{
                        alert('Ошибка: нет данных пароля');
                    }}
                }})
                .catch(err => {{
                    console.error(err);
                    alert('Ошибка при получении пароля.');
                }});
            }}
            </script>
            """,
			obj.pk,
		)

	copy_button.short_description = "Actions"

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(groups__members=request.user).distinct()

	def has_view_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True
		if obj is None:
			return GroupMembership.objects.filter(user=request.user).exists()
		return user_can_read_password(request.user, obj)

	def has_change_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True
		if obj is None:
			return GroupMembership.objects.filter(
				user=request.user, role=GroupMembership.ROLE_READ_WRITE
			).exists()
		return user_can_write_password(request.user, obj)

	def has_add_permission(self, request):
		if request.user.is_superuser:
			return True
		return GroupMembership.objects.filter(
			user=request.user, role=GroupMembership.ROLE_READ_WRITE
		).exists()

	def has_delete_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True
		if obj is None:
			return False
		return user_can_write_password(request.user, obj)

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
		if request.method != "POST":
			return JsonResponse({"error": "Only POST allowed"}, status=405)

		obj = get_object_or_404(Password, pk=object_id)

		if not (
			user_can_read_password(request.user, obj)
			or request.user.is_superuser
		):
			return JsonResponse({"error": "Permission denied"}, status=403)

		try:
			AccessLog.objects.create(
				user=request.user,
				password=obj,
				action=AccessLog.ACTION_REVEAL,
				ip_address=get_client_ip(request),
				user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
			)
		except Exception:
			pass

		try:
			clear = decrypt_password(obj.password)
		except Exception:
			clear = "[decryption failed]"

		return JsonResponse({"password": clear})

	def change_view(self, request, object_id, form_url="", extra_context=None):
		obj = get_object_or_404(Password, pk=object_id)
		if (
			user_can_read_password(request.user, obj)
			or request.user.is_superuser
		):
			try:
				AccessLog.objects.create(
					user=request.user,
					password=obj,
					action=AccessLog.ACTION_VIEW_PAGE,
					ip_address=get_client_ip(request),
					user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
				)
			except Exception:
				pass
		return super().change_view(
			request, object_id, form_url, extra_context=extra_context
		)

	def response_add(self, request, obj, post_url_continue=None):
		try:
			AccessLog.objects.create(
				user=request.user,
				password=obj,
				action=AccessLog.ACTION_CREATE,
				ip_address=get_client_ip(request),
				user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
			)
		except Exception:
			pass
		return super().response_add(
			request, obj, post_url_continue=post_url_continue
		)

	def response_change(self, request, obj):
		try:
			AccessLog.objects.create(
				user=request.user,
				password=obj,
				action=AccessLog.ACTION_CHANGE,
				ip_address=get_client_ip(request),
				user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
			)
		except Exception:
			pass
		return super().response_change(request, obj)

	def delete_model(self, request, obj):
		try:
			AccessLog.objects.create(
				user=request.user,
				password=obj,
				action=AccessLog.ACTION_DELETE,
				ip_address=get_client_ip(request),
				user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
			)
		except Exception:
			pass
		return super().delete_model(request, obj)


class GroupMembershipInline(admin.TabularInline):
	model = GroupMembership
	extra = 0
	raw_id_fields = ("user",)


@admin.register(PasswordGroup)
class PasswordGroupAdmin(admin.ModelAdmin):
	list_display = ("name", "description", "members_list")
	inlines = [GroupMembershipInline]
	filter_horizontal = ("passwords",)

	def members_list(self, obj):
		return ", ".join(
			[
				f"{m.user} ({m.get_role_display()})"
				for m in obj.memberships.all()
			]
		)

	members_list.short_description = "Members"


user_admin_site.register(Password, PasswordAdmin)
user_admin_site.register(PasswordGroup, PasswordGroupAdmin)

admin.site.register(GroupMembership)
admin.site.register(AccessLog)
