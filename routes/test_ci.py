import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User


@pytest.mark.django_db
class TestCI:
    def test_homepage(self):
        client = APIClient()
        response = client.get('/multi/')
        assert response.status_code == 200
    
    def test_api_root(self):
        client = APIClient()
        response = client.get('/api/')
        assert response.status_code == 401
    
    def test_token_endpoint_exists(self):
        url = reverse('token_obtain_pair')
        assert url == '/api/token/'