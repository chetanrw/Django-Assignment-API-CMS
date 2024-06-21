from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            password='AuthorPassword123',
            first_name='John',
            last_name='Doe',
            phone='1234567890',
        )

    def authenticate_client(self, user):
        self.client.force_authenticate(user=user)

    def test_author_registration(self):
        url = reverse('user-list')  # Assuming 'user-list' is the endpoint for user registration
        data = {
            'email': 'newauthor@example.com',
            'password': 'NewAuthorPassword123',
            'first_name': 'New',
            'last_name': 'Author',
            'phone': '9876543210',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('id' in response.data)
        self.assertEqual(response.data['email'], 'newauthor@example.com')

    def test_author_login(self):
        url = reverse('token_obtain_pair')  # Assuming 'token_obtain_pair' is the endpoint for token authentication
        data = {
            'email': 'author@example.com',
            'password': 'AuthorPassword123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

    def test_author_login_invalid_credentials(self):
        url = reverse('token_obtain_pair')  # Assuming 'token_obtain_pair' is the endpoint for token authentication
        data = {
            'email': 'author@example.com',
            'password': 'InvalidPassword',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_list_users(self):
        self.authenticate_client(self.admin)
        url = reverse('user-list')  # Assuming 'user-list' is the endpoint for listing users
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Assuming there are 2 users (admin and author)

    def test_author_cannot_list_users(self):
        self.authenticate_client(self.author)
        url = reverse('user-list')  # Assuming 'user-list' is the endpoint for listing users
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_user(self):
        self.authenticate_client(self.admin)
        user_to_delete = User.objects.create_user(
            email='delete_me@example.com',
            password='DeleteMePassword123',
        )
        url = reverse('user-detail', args=[user_to_delete.id])  # Assuming 'user-detail' is the endpoint for user detail
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user_to_delete.id).exists())

    def test_author_cannot_delete_user(self):
        self.authenticate_client(self.author)
        user_to_delete = User.objects.create_user(
            email='delete_me@example.com',
            password='DeleteMePassword123',
        )
        url = reverse('user-detail', args=[user_to_delete.id])  # Assuming 'user-detail' is the endpoint for user detail
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=user_to_delete.id).exists())

    def test_change_password(self):
        self.authenticate_client(self.author)
        url = reverse('user-change-password', args=[self.author.id])  # Assuming 'user-change-password' endpoint
        data = {
            'old_password': 'AuthorPassword123',
            'new_password': 'NewAuthorPassword456',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertTrue(self.client.login(email='author@example.com', password='NewAuthorPassword456'))

    def test_change_password_invalid_old_password(self):
        self.authenticate_client(self.author)
        url = reverse('user-change-password', args=[self.author.id])  # Assuming 'user-change-password' endpoint
        data = {
            'old_password': 'InvalidPassword',  # Ensure this is incorrect
            'new_password': 'NewAuthorPassword456',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.client.login(email='author@example.com', password='NewAuthorPassword456'))
