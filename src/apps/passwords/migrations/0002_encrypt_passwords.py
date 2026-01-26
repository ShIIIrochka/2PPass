from django.db import migrations

from apps.passwords.fields import EncryptedTextField


def encrypt_existing_passwords(apps, schema_editor):  # noqa: ARG001
    password_entry_model = apps.get_model('passwords', 'PasswordEntry')
    password_version_model = apps.get_model('passwords', 'PasswordVersion')

    prefix = 'enc:v1:'

    for model in (password_entry_model, password_version_model):
        for obj in model.objects.all().only('id', 'password').iterator(chunk_size=500):
            value = obj.password
            if not value:
                continue
            if isinstance(value, str) and value.startswith(prefix):
                continue

            obj.password = value
            obj.save(update_fields=['password'])


class Migration(migrations.Migration):
    dependencies = [
        ('passwords', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='passwordentry',
            name='password',
            field=EncryptedTextField(),
        ),
        migrations.AlterField(
            model_name='passwordversion',
            name='password',
            field=EncryptedTextField(),
        ),
        migrations.RunPython(encrypt_existing_passwords, migrations.RunPython.noop),
    ]

