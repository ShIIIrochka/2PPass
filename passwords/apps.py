# -*- coding: utf-8 -*-

from django.apps import AppConfig


class PasswordConfig(AppConfig):
	name = "passwords"
	verbose_name = "Passwords"

	def ready(self):
		from . import signals  # noqa
