class PasswordAccessLevel:
    VIEW = 'view'
    EDIT = 'edit'
    TEMPORARY = 'temporary'
    
    CHOICES = [
        (VIEW, 'Просмотр'),
        (EDIT, 'Редактирование'),
        (TEMPORARY, 'Временный доступ'),
    ]
