# -*- coding: utf-8 -*-

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
	key = getattr(settings, "PASSWORDS_FERNET_KEY", None)
	if key is None:
		raise RuntimeError("PASSWORDS_FERNET_KEY is not set in settings")
	if isinstance(key, str):
		key = key.encode()
	return Fernet(key)


def encrypt_password(plaintext: str) -> str:
	f: Fernet = _get_fernet()
	token: bytes = f.encrypt(plaintext.encode("utf-8"))
	return token.decode("utf-8")


def decrypt_password(token: str) -> str:
	f: Fernet = _get_fernet()
	try:
		from icecream import ic

		ic("try")
		return f.decrypt(token.encode("utf-8")).decode("utf-8")
	except InvalidToken:
		from icecream import ic

		ic("except")
		raise ValueError("Invalid encryption token")
