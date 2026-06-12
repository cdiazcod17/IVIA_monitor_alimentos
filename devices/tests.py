from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser
from devices.models import Device, DeviceCommand


class DeviceListViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.url = reverse('devices:list')

    def test_redirects_to_login_when_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")

    @patch('devices.views.services.check_connection')
    def test_device_list_loads_when_authenticated(self, mock_check):
        mock_check.return_value = None
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class DeviceAddViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.url = reverse('devices:add')

    def test_redirects_to_login_when_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('users:signin')}?next={self.url}")

    def test_device_add_page_loads_when_authenticated(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class SetGlobalFrequencyTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.url = reverse('devices:set_global_frequency')

    def test_redirects_to_login_when_unauthenticated(self):
        response = self.client.post(self.url, {'frequency': 5, 'power': 1})
        self.assertEqual(response.status_code, 302)

    def test_rejects_non_numeric_frequency(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.post(self.url, {'frequency': 'abc', 'power': 1})
        self.assertRedirects(response, reverse('devices:list'))
        self.assertEqual(DeviceCommand.objects.count(), 0)

    def test_clamps_frequency_above_max(self):
        self.client.login(username='test@example.com', password='testpass123')
        Device.objects.create(device_id=1, default_name='Test Device', is_active=True)
        self.client.post(self.url, {'frequency': 99999, 'power': 1})
        cmd = DeviceCommand.objects.first()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.payload['freq'], 3600)

    def test_clamps_frequency_below_min(self):
        self.client.login(username='test@example.com', password='testpass123')
        Device.objects.create(device_id=1, default_name='Test Device', is_active=True)
        self.client.post(self.url, {'frequency': 0, 'power': 1})
        cmd = DeviceCommand.objects.first()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.payload['freq'], 1)

    def test_clamps_power_to_valid_range(self):
        self.client.login(username='test@example.com', password='testpass123')
        Device.objects.create(device_id=1, default_name='Test Device', is_active=True)
        self.client.post(self.url, {'frequency': 10, 'power': 99})
        cmd = DeviceCommand.objects.first()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.payload['power'], 1)
