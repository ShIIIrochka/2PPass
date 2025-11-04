# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

from passwords.models.password import Password


class PasswordAdminForm(forms.ModelForm):
	password_plain = forms.CharField(
		required=False,
		label=_("Plain password"),
		widget=forms.PasswordInput(render_value=False),
		help_text=_("Напишите новый пароль (оставьте пустым, чтобы не менять)"),
	)

	class Meta:
		model = Password
		exclude = ("password",)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.cleaned_data.get("password_plain"):
			instance.set_password(self.cleaned_data["password_plain"])
		if commit:
			instance.save()
			self.save_m2m()
		return instance

	def clean(self):
		cleaned_data = super().clean()
		password_plain = cleaned_data.get("password_plain")

		if self.instance.pk is None and not password_plain:
			raise forms.ValidationError(_("Password required."))

		return cleaned_data
