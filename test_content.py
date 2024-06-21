from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from cms_api.models import ContentItem, Category

User = get_user_model()

class ContentManagementTests(TestCase):

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
        self.category1 = Category.objects.create(name='Category 1')
        self.category2 = Category.objects.create(name='Category 2')
        self.content1 = ContentItem.objects.create(
            title='Test Content 1',
            body='Body of test content 1',
            summary='Summary of test content 1',
            document='path/to/test.pdf',  # Adjust as per your setup
        )
        self.content1.categories.add(self.category1)

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

    def test_admin_view_all_contents(self):
        self.authenticate_client(self.admin)
        url = reverse('contentitem-list')  # Assuming 'contentitem-list' is the endpoint for content items
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Adjust as per your setup

    def test_author_create_content(self):
        self.authenticate_client(self.author)
        url = reverse('contentitem-list')
        data = {
            'title': 'New Content',
            'body': 'Body of new content',
            'summary': 'Summary of new content',
            'document': 'path/to/new.pdf',  # Adjust as per your setup
            'categories': [self.category1.id, self.category2.id],
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('id' in response.data)
        self.assertEqual(response.data['title'], 'New Content')

    def test_author_edit_own_content(self):
        self.authenticate_client(self.author)
        url = reverse('contentitem-detail', args=[self.content1.id])
        data = {
            'title': 'Updated Content',
            'body': 'Updated body of content',
            'summary': 'Updated summary of content',
            'categories': [self.category2.id],
        }
        response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.content1.refresh_from_db()
        self.assertEqual(self.content1.title, 'Updated Content')

    def test_author_delete_own_content(self):
        self.authenticate_client(self.author)
        url = reverse('contentitem-detail', args=[self.content1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ContentItem.objects.filter(id=self.content1.id).exists())

    def test_search_content_by_title(self):
        url = reverse('contentitem-list') + '?search=Test Content 1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Content 1')
