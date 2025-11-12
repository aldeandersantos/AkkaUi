import pytest
import os
from django.contrib.auth import get_user_model
from core.models import SvgFile
from payment.models import Payment, Purchase
from usuario.models import Favorite
from decimal import Decimal

os.environ.setdefault('PROD', 'False')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test_db.sqlite3')

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123'
    )


@pytest.fixture
def vip_user(db):
    return User.objects.create_user(
        username='vipuser',
        email='vip@test.com',
        password='testpass123',
        is_vip=True
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='adminuser',
        email='admin@test.com',
        password='testpass123',
        admin=True
    )


@pytest.fixture
def svg_file(user):
    return SvgFile.objects.create(
        title_name='Test SVG',
        content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>',
        owner=user,
        is_public=True,
        price=Decimal('10.00')
    )


@pytest.fixture
def free_svg(user):
    return SvgFile.objects.create(
        title_name='Free SVG',
        content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="red"/></svg>',
        owner=user,
        is_public=True,
        price=Decimal('0.00')
    )


@pytest.fixture
def payment(user):
    return Payment.objects.create(
        user=user,
        gateway='abacatepay',
        plan='pro_month',
        amount=Decimal('9.90'),
        currency='BRL',
        status='pending'
    )


@pytest.fixture
def purchase(user, svg_file):
    return Purchase.objects.create(
        user=user,
        svg=svg_file,
        price=Decimal('10.00'),
        payment_method='credit_card'
    )
