# -*- coding: utf-8 -*-

from django.db import models
from django.db.transaction import atomic
from passwords.utils.crypto import decrypt_password, encrypt_password


class Password(models.Model):
	title = models.CharField(max_length=255)
	url = models.CharField(max_length=255, null=True)
	password = models.TextField()
	note = models.TextField(blank=True, null=True)
	in_trash = models.BooleanField(default=False)

	@atomic
	def move_to_trash(self):
		self.in_trash = True
		self.save()

	@atomic
	def restore_from_trash(self):
		self.in_trash = False
		self.save()

	def set_password(self, plain_text: str) -> None:
		self.password = encrypt_password(plain_text)

	def get_password(self) -> str:
		return decrypt_password(self.password)

	def save(self, *args, **kwargs):
		if self.password and not self.password.startswith("gAAAA"):
			self.password = encrypt_password(self.password)
		super().save(*args, **kwargs)

	def __str__(self) -> str:
		return str(self.title)


class PasswordInTrash(Password):
	class Meta:
		proxy = True
		verbose_name = "Пароль (корзина)"
		verbose_name_plural = "Корзина"
