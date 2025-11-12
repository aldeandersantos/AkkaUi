import pytest
from django.contrib.auth import get_user_model
from usuario.models import CustomUser, Favorite

User = get_user_model()


@pytest.mark.models
@pytest.mark.django_db
class TestCustomUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username='newuser',
            email='new@test.com',
            password='password123'
        )
        assert user.username == 'newuser'
        assert user.email == 'new@test.com'
        assert user.check_password('password123')
    
    def test_user_hash_id_generation(self):
        user = User.objects.create_user(
            username='hashuser',
            password='pass123'
        )
        assert user.hash_id is not None
        assert len(user.hash_id) == 64
    
    def test_user_hash_id_unique(self):
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        assert user1.hash_id != user2.hash_id
    
    def test_user_hash_id_preserved_on_update(self):
        user = User.objects.create_user(username='testuser', password='pass')
        original_hash = user.hash_id
        user.email = 'updated@test.com'
        user.save()
        assert user.hash_id == original_hash
    
    def test_user_default_values(self):
        user = User.objects.create_user(username='defaults', password='pass')
        assert user.is_active is True
        assert user.is_vip is False
        assert user.admin is False
        assert user.vip_expiration is None
        assert user.stripe_customer_id is None
        assert user.stripe_subscription_id is None
    
    def test_user_str_representation(self, user):
        assert str(user) == user.username
    
    def test_user_vip_fields(self):
        from datetime import date, timedelta
        expiration_date = date.today() + timedelta(days=30)
        
        user = User.objects.create_user(
            username='vipuser',
            password='pass',
            is_vip=True,
            vip_expiration=expiration_date,
            stripe_customer_id='cus_test123',
            stripe_subscription_id='sub_test123'
        )
        
        assert user.is_vip is True
        assert user.vip_expiration == expiration_date
        assert user.stripe_customer_id == 'cus_test123'
        assert user.stripe_subscription_id == 'sub_test123'
    
    def test_user_admin_field(self):
        user = User.objects.create_user(
            username='adminuser',
            password='pass',
            admin=True
        )
        assert user.admin is True
    
    def test_user_phone_field(self):
        user = User.objects.create_user(
            username='phoneuser',
            password='pass',
            phone='11999999999'
        )
        assert user.phone == '11999999999'


@pytest.mark.models
@pytest.mark.django_db
class TestFavoriteModel:
    def test_create_favorite(self, user):
        favorite = Favorite.objects.create(
            user=user,
            svg_ids=[1, 2, 3]
        )
        assert favorite.user == user
        assert favorite.svg_ids == [1, 2, 3]
    
    def test_favorite_default_empty_list(self, user):
        favorite = Favorite.objects.create(user=user)
        assert favorite.svg_ids == []
    
    def test_favorite_str_representation(self, user):
        favorite = Favorite.objects.create(user=user)
        assert user.username in str(favorite)
    
    def test_favorite_one_to_one_relationship(self, user):
        favorite1 = Favorite.objects.create(user=user)
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Favorite.objects.create(user=user)
    
    def test_favorite_update_svg_ids(self, user):
        favorite = Favorite.objects.create(user=user, svg_ids=[1])
        favorite.svg_ids.append(2)
        favorite.save()
        
        favorite.refresh_from_db()
        assert favorite.svg_ids == [1, 2]
    
    def test_favorite_timestamps(self, user):
        favorite = Favorite.objects.create(user=user)
        assert favorite.created_at is not None
        assert favorite.updated_at is not None
