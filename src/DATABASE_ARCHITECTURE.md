# Архитектура баз данных 2PPass

## PostgreSQL - Единая база данных

Проект использует **PostgreSQL** для всех данных через стандартный Django ORM.

### Django ORM модели
- **User** - пользователи системы (кастомная модель пользователя)
- **Vault** - хранилища паролей
- **VaultAccess** - доступы пользователей к хранилищам
- **PasswordEntry** - записи паролей
- **PasswordVersion** - история изменений паролей
- **AuditLog** - журнал аудита
- **CustomRole** - кастомные роли
- **Permission** - разрешения для ролей

### Преимущества
- Единая база данных для всех данных
- Полная поддержка Django ORM
- ACID транзакции
- Надежность и производительность
- Полная поддержка миграций Django
- Поддержка сложных запросов и связей

## Работа с моделями

### Django ORM операции
```python
from apps.users.models import User
from apps.vaults.models import Vault
from apps.passwords.models import PasswordEntry

# Создание пользователя
user = User.objects.create_user(
    email='test@example.com',
    password='raw_password'
)

# Аутентификация
from django.contrib.auth import authenticate
user = authenticate(request, username='test@example.com', password='password')

# Работа с хранилищами
vault = Vault.objects.create(name='Мое хранилище', created_by=user)
passwords = PasswordEntry.objects.filter(vault=vault, is_deleted=False)
```

## Аутентификация

Используется стандартный Django ModelBackend с кастомной моделью User:
- Поддержка аутентификации по email (USERNAME_FIELD = 'email')
- Интеграция с Django sessions
- Полная совместимость с Django auth middleware
- Поддержка стандартных методов Django (authenticate, login, logout)

## Миграции

**PostgreSQL полностью поддерживает миграции Django**:
```bash
python manage.py makemigrations
python manage.py migrate
```

Миграции создают таблицы, индексы и ограничения в PostgreSQL автоматически.

## Настройка PostgreSQL

Настройки в `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '2ppass',
        'USER': '2ppass',
        'PASSWORD': '2ppass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Подключение происходит автоматически при старте Django приложения.

## Docker Compose

PostgreSQL запускается через Docker Compose:
```bash
docker compose up -d postgres
```
