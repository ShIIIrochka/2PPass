# -*- coding: utf-8 -*-

from django.utils.html import format_html


def groups_list(self, obj):
	return ", ".join([g.name for g in obj.groups.all()])


groups_list.short_description = "Groups"


def masked_password(self, obj):
	return "••••••••"


masked_password.short_description = "Password (masked)"


def copy_button(self, obj):
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
		obj.pk,
	)


copy_button.short_description = "Actions"
