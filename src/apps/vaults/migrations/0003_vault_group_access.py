from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
        ('vaults', '0002_alter_vault_accesses'),
    ]

    operations = [
        migrations.CreateModel(
            name='VaultGroupAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_level', models.CharField(choices=[('view', 'Просмотр'), ('edit', 'Редактирование'), ('admin', 'Администратор')], max_length=10)),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('granted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='granted_group_accesses', to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vault_accesses', to='auth.group')),
                ('vault', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_access_list', to='vaults.vault')),
            ],
            options={
                'db_table': 'vault_group_accesses',
            },
        ),
        migrations.AlterUniqueTogether(
            name='vaultgroupaccess',
            unique_together={('vault', 'group')},
        ),
    ]

