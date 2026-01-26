import base64
from functools import lru_cache
from typing import Iterable, List, Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


ENC_PREFIX = "enc:v1:"


def is_encrypted(value: Optional[str]) -> bool:
    return bool(value) and isinstance(value, str) and value.startswith(ENC_PREFIX)


def _normalize_keys(keys: Iterable[str]) -> List[bytes]:
    normalized: List[bytes] = []
    for raw in keys:
        key = (raw or "").strip()
        if not key:
            continue
        try:
            key_bytes = key.encode("utf-8")
        except Exception as e:
            raise ImproperlyConfigured("VAULT_ENCRYPTION_KEYS содержит некорректный ключ.") from e

        try:
            decoded = base64.urlsafe_b64decode(key_bytes)
        except Exception as e:
            raise ImproperlyConfigured("VAULT_ENCRYPTION_KEYS содержит невалидный base64url ключ Fernet.") from e

        if len(decoded) != 32:
            raise ImproperlyConfigured("VAULT_ENCRYPTION_KEYS: ключ Fernet должен декодироваться в 32 байта.")

        normalized.append(key_bytes)

    if not normalized:
        raise ImproperlyConfigured("Не задан VAULT_ENCRYPTION_KEYS. Добавьте ключ шифрования в окружение.")

    return normalized


@lru_cache(maxsize=1)
def get_fernet() -> MultiFernet:
    keys = getattr(settings, "VAULT_ENCRYPTION_KEYS", None)
    if keys is None:
        raise ImproperlyConfigured("Отсутствует настройка VAULT_ENCRYPTION_KEYS.")

    key_bytes = _normalize_keys(keys)
    fernets = [Fernet(k) for k in key_bytes]
    return MultiFernet(fernets)


def encrypt_str(plaintext: str) -> str:
    token = get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{ENC_PREFIX}{token}"


def decrypt_str(value: str) -> str:
    if not is_encrypted(value):
        return value

    token = value[len(ENC_PREFIX) :]
    try:
        return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise ImproperlyConfigured("Не удалось расшифровать значение: неверный ключ VAULT_ENCRYPTION_KEYS.") from e

