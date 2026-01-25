class UserRole:
    ADMIN = 'admin'
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    
    CHOICES = [
        (ADMIN, 'Администратор'),
        (MANAGER, 'Менеджер'),
        (EMPLOYEE, 'Сотрудник'),
    ]
