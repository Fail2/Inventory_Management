from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Supplier


class AddSupplierEmailFallbackTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123',
        )

    @patch('accounts.views.EmailMultiAlternatives.send', side_effect=Exception('SMTP auth failed'))
    def test_supplier_is_created_when_welcome_email_fails(self, mocked_send):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('add_user', kwargs={'user_type': 'supplier'}),
            {
                'full_name': 'Test Supplier',
                'address': '123 Supplier Street',
                'email': 'supplier@example.com',
                'username': 'supplier1',
                'password': 'StrongPass123',
                'confirm_password': 'StrongPass123',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(email='supplier@example.com').exists())
