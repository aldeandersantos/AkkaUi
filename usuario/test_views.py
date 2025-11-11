import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from usuario.models import CustomUser
import base64

User = get_user_model()


@pytest.mark.views
@pytest.mark.django_db
class TestSignupView:
    def test_signup_page_loads(self, client):
        response = client.get(reverse('usuario:signup'))
        assert response.status_code == 200
    
    def test_signup_redirects_if_authenticated(self, client, user):
        client.force_login(user)
        response = client.get(reverse('usuario:signup'))
        assert response.status_code == 302
    
    def test_signup_creates_user(self, client):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = client.post(reverse('usuario:signup'), data)
        
        assert response.status_code == 302
        assert User.objects.filter(username='newuser').exists()
    
    def test_signup_validation_username_required(self, client):
        data = {
            'username': '',
            'email': 'test@test.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = client.post(reverse('usuario:signup'), data)
        assert response.status_code == 200
    
    def test_signup_validation_username_too_short(self, client):
        data = {
            'username': 'ab',
            'email': 'test@test.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = client.post(reverse('usuario:signup'), data)
        assert response.status_code == 200
    
    def test_signup_validation_duplicate_username(self, client, user):
        data = {
            'username': user.username,
            'email': 'another@test.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = client.post(reverse('usuario:signup'), data)
        assert response.status_code == 200
    
    def test_signup_validation_password_mismatch(self, client):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'password_confirm': 'different123'
        }
        response = client.post(reverse('usuario:signup'), data)
        assert response.status_code == 200
    
    def test_signup_validation_password_too_short(self, client):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': '12345',
            'password_confirm': '12345'
        }
        response = client.post(reverse('usuario:signup'), data)
        assert response.status_code == 200
    
    def test_signup_with_phone(self, client):
        data = {
            'username': 'phoneuser',
            'email': 'phone@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'phone': '11999999999'
        }
        response = client.post(reverse('usuario:signup'), data)
        
        assert response.status_code == 302
        user = User.objects.get(username='phoneuser')
        assert user.phone == '11999999999'


@pytest.mark.views
@pytest.mark.django_db
class TestSigninView:
    def test_signin_page_loads(self, client):
        response = client.get(reverse('usuario:signin'))
        assert response.status_code == 200
    
    def test_signin_redirects_if_authenticated(self, client, user):
        client.force_login(user)
        response = client.get(reverse('usuario:signin'))
        assert response.status_code == 302
    
    def test_signin_success(self, client, user):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = client.post(reverse('usuario:signin'), data)
        assert response.status_code == 302
    
    def test_signin_invalid_credentials(self, client, user):
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = client.post(reverse('usuario:signin'), data)
        assert response.status_code == 200


@pytest.mark.views
@pytest.mark.django_db
class TestGetTokenView:
    def test_get_token_success(self, client, user):
        credentials = f"{user.username}:testpass123"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        response = client.post(
            reverse('usuario:get_token'),
            HTTP_AUTHORIZATION=f'Basic {encoded}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert data['token_type'] == 'signed'
    
    def test_get_token_missing_auth_header(self, client):
        response = client.post(reverse('usuario:get_token'))
        assert response.status_code == 400
    
    def test_get_token_invalid_credentials(self, client, user):
        credentials = f"{user.username}:wrongpassword"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        response = client.post(
            reverse('usuario:get_token'),
            HTTP_AUTHORIZATION=f'Basic {encoded}'
        )
        
        assert response.status_code == 401
    
    def test_get_token_malformed_basic_auth(self, client):
        response = client.post(
            reverse('usuario:get_token'),
            HTTP_AUTHORIZATION='Basic invalid'
        )
        assert response.status_code == 400


@pytest.mark.views
@pytest.mark.django_db
class TestAdminRequired:
    def test_admin_required_denies_non_admin(self, client, user):
        from usuario.views.views_usuario import admin_required
        from django.http import HttpResponse
        
        @admin_required
        def test_view(request):
            return HttpResponse('OK')
        
        client.force_login(user)
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = user
        
        response = test_view(request)
        assert response.status_code == 403
    
    def test_admin_required_allows_admin(self, client, admin_user):
        from usuario.views.views_usuario import admin_required
        from django.http import HttpResponse
        
        @admin_required
        def test_view(request):
            return HttpResponse('OK')
        
        client.force_login(admin_user)
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = admin_user
        
        response = test_view(request)
        assert response.status_code == 200
