import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from core.models import SvgFile

User = get_user_model()


@pytest.mark.models
@pytest.mark.django_db
class TestSvgFileModel:
    def test_create_svg_file(self, user):
        svg = SvgFile.objects.create(
            title_name='Test SVG',
            content='<svg></svg>',
            owner=user,
            is_public=True,
            price=Decimal('10.00')
        )
        assert svg.title_name == 'Test SVG'
        assert svg.owner == user
        assert svg.price == Decimal('10.00')
        assert svg.is_public is True
    
    def test_svg_file_str_representation(self, svg_file):
        assert svg_file.title_name in str(svg_file)
    
    def test_svg_hash_generation_on_create(self, user):
        svg = SvgFile.objects.create(
            title_name='Hash Test',
            content='<svg></svg>',
            owner=user
        )
        assert svg.hash_value is not None
        assert len(svg.hash_value) == 64
    
    def test_svg_hash_unique_constraint(self, user):
        svg1 = SvgFile.objects.create(
            title_name='SVG 1',
            content='<svg></svg>',
            owner=user
        )
        hash1 = svg1.hash_value
        
        svg2 = SvgFile.objects.create(
            title_name='SVG 2',
            content='<svg></svg>',
            owner=user
        )
        assert svg1.hash_value != svg2.hash_value
    
    def test_get_thumbnail_url_with_thumbnail(self, svg_file, mocker):
        mocker.patch.object(svg_file, 'thumbnail', True)
        url = svg_file.get_thumbnail_url()
        assert url is not None
        assert 'thumbnail' in url
    
    def test_get_thumbnail_url_without_thumbnail(self, svg_file):
        svg_file.thumbnail = None
        url = svg_file.get_thumbnail_url()
        assert url is None
    
    def test_user_access_type_anonymous_free_svg(self, free_svg):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        assert free_svg.user_access_type(anon) == 'free'
    
    def test_user_access_type_anonymous_paid_svg(self, svg_file):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        assert svg_file.user_access_type(anon) == 'locked'
    
    def test_user_access_type_vip_paid_svg(self, vip_user, svg_file):
        assert svg_file.user_access_type(vip_user) == 'vip'
    
    def test_user_access_type_vip_free_svg(self, vip_user, free_svg):
        assert free_svg.user_access_type(vip_user) == 'free'
    
    def test_user_access_type_owned(self, user, svg_file, purchase):
        assert svg_file.user_access_type(user) == 'owned'
    
    def test_user_access_type_locked(self, svg_file):
        other_user = User.objects.create_user(
            username='otheruser',
            password='pass123'
        )
        assert svg_file.user_access_type(other_user) == 'locked'
    
    def test_user_access_type_free_svg_authenticated(self, user, free_svg):
        assert free_svg.user_access_type(user) == 'free'
    
    def test_get_sanitized_content_removes_script_tags(self, user):
        svg = SvgFile.objects.create(
            title_name='Malicious SVG',
            content='<svg><script>alert("XSS")</script><circle/></svg>',
            owner=user
        )
        sanitized = svg.get_sanitized_content()
        assert '<script>' not in sanitized
        assert 'alert' not in sanitized
        assert '<circle/>' in sanitized
    
    def test_get_sanitized_content_removes_event_handlers(self, user):
        svg = SvgFile.objects.create(
            title_name='Event Handler SVG',
            content='<svg><circle onclick="alert()" onload="evil()"/></svg>',
            owner=user
        )
        sanitized = svg.get_sanitized_content()
        assert 'onclick' not in sanitized
        assert 'onload' not in sanitized
    
    def test_svg_default_values(self, user):
        svg = SvgFile.objects.create(
            title_name='Defaults Test',
            content='<svg></svg>',
            owner=user
        )
        assert svg.is_public is False
        assert svg.price == Decimal('0.00')
        assert svg.filename == ""
