from __future__ import annotations

from django.db import models

from apps.passwords.crypto import decrypt_str, encrypt_str, is_encrypted


class EncryptedTextField(models.TextField):
    def from_db_value(self, value, expression, connection):  # noqa: ANN001
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return decrypt_str(value)

    def to_python(self, value):  # noqa: ANN001
        if value is None or isinstance(value, str) and not value:
            return value
        if not isinstance(value, str):
            value = str(value)
        return decrypt_str(value)

    def get_prep_value(self, value):  # noqa: ANN001
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)

        if is_encrypted(value):
            decrypt_str(value)
            return value

        if value == "":
            return value

        return encrypt_str(value)

