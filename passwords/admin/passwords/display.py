# -*- coding: utf-8 -*-

from typing import Any

from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


def groups_list(self, obj: Any) -> str:
	"""Список имён групп через запятую."""
	return ", ".join(g.name for g in obj.groups.all())


groups_list.short_description = _("Группы")


def masked_password(self, obj: Any) -> str:
	"""Скрытое представление пароля."""
	return "••••••••"


masked_password.short_description = _("Пароль (скрыт)")


def copy_button(self, obj: Any) -> str:
	"""Кнопка для копирования пароля в буфер обмена."""
	pk = getattr(obj, "pk", None)
	if pk is None:
		return ""
	return format_html(
		"""
		<button type="button" class="button" onclick="copyPassword{0}()">Copy password</button>
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
                    navigator.clipboard.writeText(data.password);
                    alert('Password copied!');
                }} else {{
                    alert('Password not found.');
                }}
            }})
            .catch(() => alert('Something went wrong.'));
        }}
        </script>
        """,
		pk,
	)


copy_button.short_description = _("Действия")
