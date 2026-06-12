from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser


class SigninViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.url = reverse('users:signin')

    def test_signin_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_signin_valid_credentials_redirects(self):
        response = self.client.post(self.url, {
            'username': 'test@example.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('devices:list'))

    def test_signin_invalid_credentials_stays_on_page(self):
        response = self.client.post(self.url, {
            'username': 'test@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class SignupViewTest(TestCase):
    def setUp(self):
        self.url = reverse('users:signup')

    def test_signup_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user_and_redirects(self):
        response = self.client.post(self.url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'New',
            'last_name': 'User',
        })
        self.assertTrue(CustomUser.objects.filter(email='new@example.com').exists())
        self.assertRedirects(response, reverse('devices:list'))


class SignoutViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )

    def test_signout_redirects_to_home(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('users:signout'))
        self.assertRedirects(response, reverse('home'))

    def test_user_is_logged_out_after_signout(self):
        self.client.login(username='test@example.com', password='testpass123')
        self.client.get(reverse('users:signout'))
        response = self.client.get(reverse('devices:list'))
        self.assertRedirects(
            response,
            f"{reverse('users:signin')}?next={reverse('devices:list')}"
        )
