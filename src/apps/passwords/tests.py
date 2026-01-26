from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings

from apps.passwords.crypto import get_fernet
from apps.passwords.models import PasswordEntry, PasswordVersion
from apps.vaults.models import Vault


User = get_user_model()


class PasswordEncryptionTests(TestCase):
    def setUp(self):
        super().setUp()
        get_fernet.cache_clear()

    def tearDown(self):
        get_fernet.cache_clear()
        super().tearDown()

    def test_password_entry_stores_ciphertext_returns_plaintext(self):
        key = Fernet.generate_key().decode('utf-8')

        with override_settings(VAULT_ENCRYPTION_KEYS=[key]):
            get_fernet.cache_clear()

            user = User.objects.create_user(email='user@example.com', password='pass12345')
            vault = Vault.objects.create(
                name='Test vault',
                description='',
                created_by=user,
                tags=[],
            )

            entry = PasswordEntry.objects.create(
                vault=vault,
                title='Title',
                login='login',
                password='super-secret',
                url='',
                notes='',
                tags=[],
                created_by=user,
            )

            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM passwords WHERE id = %s", [entry.id])
                stored = cursor.fetchone()[0]

            self.assertTrue(isinstance(stored, str))
            self.assertTrue(stored.startswith('enc:v1:'))
            self.assertNotIn('super-secret', stored)

            entry.refresh_from_db()
            self.assertEqual(entry.password, 'super-secret')

    def test_password_version_stores_ciphertext_returns_plaintext(self):
        key = Fernet.generate_key().decode('utf-8')

        with override_settings(VAULT_ENCRYPTION_KEYS=[key]):
            get_fernet.cache_clear()

            user = User.objects.create_user(email='user2@example.com', password='pass12345')
            vault = Vault.objects.create(
                name='Test vault',
                description='',
                created_by=user,
                tags=[],
            )
            entry = PasswordEntry.objects.create(
                vault=vault,
                title='Title',
                login='login',
                password='super-secret',
                url='',
                notes='',
                tags=[],
                created_by=user,
            )

            version = PasswordVersion.objects.create(
                password_entry=entry,
                version='v1',
                login='login',
                password='super-secret-v',
                url='',
                notes='',
                tags=[],
                created_by=user,
            )

            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM password_versions WHERE id = %s", [version.id])
                stored = cursor.fetchone()[0]

            self.assertTrue(isinstance(stored, str))
            self.assertTrue(stored.startswith('enc:v1:'))
            self.assertNotIn('super-secret-v', stored)

            version.refresh_from_db()
            self.assertEqual(version.password, 'super-secret-v')
