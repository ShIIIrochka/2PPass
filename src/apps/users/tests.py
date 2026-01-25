from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.constants import UserRole
from apps.users.models import User


class UserCreateTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role=UserRole.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.manager = User.objects.create_user(
            email='manager@example.com',
            password='managerpass123',
            role=UserRole.MANAGER,
            is_staff=True,
        )

    def test_manager_cannot_create_admin(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/users/', data={
            'email': 'newadmin@example.com',
            'role': UserRole.ADMIN,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_can_create_employee(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/users/', data={
            'email': 'employee@example.com',
            'role': UserRole.EMPLOYEE,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], UserRole.EMPLOYEE)

    def test_admin_can_create_manager(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/users/', data={
            'email': 'newmanager@example.com',
            'role': UserRole.MANAGER,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], UserRole.MANAGER)


class UserListTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin2@example.com',
            password='adminpass123',
            role=UserRole.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.manager = User.objects.create_user(
            email='manager2@example.com',
            password='managerpass123',
            role=UserRole.MANAGER,
            is_staff=True,
        )
        User.objects.create_user(email='emp1@example.com', password='emp12345', role=UserRole.EMPLOYEE)
        User.objects.create_user(email='emp2@example.com', password='emp12345', role=UserRole.EMPLOYEE)

    def test_manager_sees_only_employees(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        roles = {item['role'] for item in results}
        self.assertEqual(roles, {UserRole.EMPLOYEE})


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='temppass123',
            role=UserRole.EMPLOYEE,
            password_changed=False,
        )

    def test_login_with_temporary_password(self):
        response = self.client.post('/api/users/login/', data={
            'email': 'employee@example.com',
            'password': 'temppass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'employee@example.com')
        self.assertFalse(response.data['password_changed'])

    def test_login_with_invalid_credentials(self):
        response = self.client.post('/api/users/login/', data={
            'email': 'employee@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/users/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordChangeTests(APITestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='temppass123',
            role=UserRole.EMPLOYEE,
            password_changed=False,
        )

    def test_password_change_with_temporary_password(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/users/password-change/', data={
            'old_password': 'temppass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.password_changed)
        self.assertTrue(self.employee.check_password('newpass123'))

    def test_password_change_with_wrong_old_password(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/users/password-change/', data={
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_with_mismatched_passwords(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/users/password-change/', data={
            'old_password': 'temppass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'differentpass',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_already_changed(self):
        self.employee.password_changed = True
        self.employee.save()
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/users/password-change/', data={
            'old_password': 'temppass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileUpdateTests(APITestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='temppass123',
            role=UserRole.EMPLOYEE,
            password_changed=True,
        )

    def test_get_profile(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('phone', response.data)

    def test_update_profile_after_password_change(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch('/api/users/profile/', data={
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'phone': '+79001234567',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Иван')
        self.assertEqual(response.data['last_name'], 'Иванов')
        self.assertEqual(response.data['phone'], '+79001234567')
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, 'Иван')
        self.assertEqual(self.employee.last_name, 'Иванов')
        self.assertEqual(self.employee.phone, '+79001234567')

    def test_update_profile_before_password_change(self):
        self.employee.password_changed = False
        self.employee.save()
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch('/api/users/profile/', data={
            'first_name': 'Иван',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
