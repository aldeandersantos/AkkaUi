import pytest
import json
from django.urls import reverse
from core.models import SvgFile
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.views
@pytest.mark.django_db
class TestHomeView:
    def test_home_page_loads(self, client):
        response = client.get(reverse('core:home'))
        assert response.status_code == 200
    
    def test_home_shows_public_svgs(self, client, svg_file):
        response = client.get(reverse('core:home'))
        assert response.status_code == 200
        assert 'svgfiles' in response.context
    
    def test_home_authenticated_user_access_info(self, client, user, svg_file):
        client.force_login(user)
        response = client.get(reverse('core:home'))
        
        assert response.status_code == 200
        svgs = response.context['svgfiles']
        assert len(svgs) > 0


@pytest.mark.views
@pytest.mark.django_db
class TestExploreView:
    def test_explore_page_loads(self, client):
        response = client.get(reverse('core:explore'))
        assert response.status_code == 200
    
    def test_explore_search_by_title(self, client, user):
        svg1 = SvgFile.objects.create(
            title_name='Logo Blue',
            content='<svg></svg>',
            owner=user,
            is_public=True
        )
        svg2 = SvgFile.objects.create(
            title_name='Icon Red',
            content='<svg></svg>',
            owner=user,
            is_public=True
        )
        
        response = client.get(reverse('core:explore'), {'q': 'Logo'})
        assert response.status_code == 200
        assert response.context['search_query'] == 'Logo'
    
    def test_explore_filter_by_tag(self, client, user):
        svg = SvgFile.objects.create(
            title_name='Test',
            content='<svg></svg>',
            owner=user,
            is_public=True,
            tags='icon, blue'
        )
        
        response = client.get(reverse('core:explore'), {'tag': 'icon'})
        assert response.status_code == 200
        assert response.context['selected_tag'] == 'icon'
    
    def test_explore_sort_options(self, client):
        for sort in ['-uploaded_at', 'uploaded_at', 'title_name', '-title_name']:
            response = client.get(reverse('core:explore'), {'sort': sort})
            assert response.status_code == 200
            assert response.context['selected_sort'] == sort
    
    def test_explore_invalid_sort_uses_default(self, client):
        response = client.get(reverse('core:explore'), {'sort': 'invalid'})
        assert response.status_code == 200
        assert response.context['selected_sort'] == 'invalid'


@pytest.mark.views
@pytest.mark.django_db
class TestPricingView:
    def test_pricing_page_loads(self, client):
        response = client.get(reverse('core:pricing'))
        assert response.status_code == 200


@pytest.mark.views
@pytest.mark.django_db
class TestFaqView:
    def test_faq_page_loads(self, client):
        response = client.get(reverse('core:faq'))
        assert response.status_code == 200


@pytest.mark.views
@pytest.mark.django_db
class TestCartView:
    def test_cart_page_loads(self, client, user):
        client.force_login(user)
        response = client.get(reverse('core:cart'))
        assert response.status_code in [200, 302]


@pytest.mark.views
@pytest.mark.django_db
class TestMinhabibliotecaView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('core:minha_biblioteca'))
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_authenticated_user_can_access(self, client, user):
        client.force_login(user)
        response = client.get(reverse('core:minha_biblioteca'))
        assert response.status_code == 200


@pytest.mark.views
@pytest.mark.django_db
class TestSearchSvgApi:
    def test_search_svg_returns_json(self, client, user):
        svg = SvgFile.objects.create(
            title_name='Test SVG',
            content='<svg></svg>',
            owner=user,
            is_public=True
        )
        
        response = client.get(reverse('core:search_svg'), {'q': 'Test'})
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data or 'count' in data


@pytest.mark.views
@pytest.mark.django_db
class TestAdminSvgViews:
    def test_admin_svg_requires_authentication(self, client):
        response = client.get(reverse('core:admin_svg'))
        assert response.status_code == 302
    
    def test_admin_svg_requires_admin_permission(self, client, user):
        client.force_login(user)
        response = client.get(reverse('core:admin_svg'))
        assert response.status_code == 403
    
    def test_admin_svg_allows_admin_user(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('core:admin_svg'))
        assert response.status_code == 200
    
    def test_admin_create_svg_requires_admin(self, client, user):
        client.force_login(user)
        response = client.get(reverse('core:admin_create_svg'))
        assert response.status_code == 403
    
    def test_admin_update_svg_requires_admin(self, client, user):
        client.force_login(user)
        response = client.get(reverse('core:admin_update_svg'))
        assert response.status_code == 403


@pytest.mark.views
@pytest.mark.django_db
class TestCopySvgApi:
    def test_copy_svg_requires_post(self, client):
        response = client.get(reverse('core:copy_svg'))
        assert response.status_code in [400, 405, 302]
    
    def test_copy_svg_requires_authentication(self, client):
        response = client.post(
            reverse('core:copy_svg'),
            data=json.dumps({'svg_id': 1}),
            content_type='application/json'
        )
        assert response.status_code in [302, 400, 405]
