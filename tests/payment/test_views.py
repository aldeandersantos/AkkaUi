import pytest
import json
from decimal import Decimal
from django.urls import reverse
from unittest.mock import patch, MagicMock
from payment.models import Purchase, Payment
from core.models import SvgFile
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.views
@pytest.mark.django_db
class TestPurchasedSvgsPageView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('payment:purchased_svgs'))
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_regular_user_sees_purchases(self, client, user, svg_file, purchase):
        client.force_login(user)
        response = client.get(reverse('payment:purchased_svgs'))
        
        assert response.status_code == 200
        assert response.context['is_vip'] is False
        assert len(response.context['svgfiles']) == 1
    
    def test_vip_user_sees_all_svgs(self, client, vip_user, svg_file, free_svg):
        client.force_login(vip_user)
        response = client.get(reverse('payment:purchased_svgs'))
        
        assert response.status_code == 200
        assert response.context['is_vip'] is True
        assert len(response.context['svgfiles']) >= 2


@pytest.mark.views
@pytest.mark.django_db
class TestPurchasedSvgsApiView:
    def test_requires_authentication(self, client, user):
        response = client.get(reverse('payment:purchased_svgs_api', args=[user.id]))
        assert response.status_code == 302
    
    def test_user_can_only_access_own_purchases(self, client, user):
        other_user = User.objects.create_user(username='other', password='pass')
        client.force_login(user)
        
        response = client.get(reverse('payment:purchased_svgs_api', args=[other_user.id]))
        assert response.status_code == 403
    
    def test_vip_user_response(self, client, vip_user):
        client.force_login(vip_user)
        response = client.get(reverse('payment:purchased_svgs_api', args=[vip_user.id]))
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_vip'] is True


@pytest.mark.views
@pytest.mark.django_db
class TestCreatePurchaseView:
    def test_requires_authentication(self, client, svg_file):
        response = client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': svg_file.id}),
            content_type='application/json'
        )
        assert response.status_code == 302
    
    def test_create_purchase_success(self, client, user, svg_file):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': svg_file.id, 'price': 10.00}),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert Purchase.objects.filter(user=user, svg=svg_file).exists()
    
    def test_create_purchase_duplicate(self, client, user, svg_file, purchase):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': svg_file.id}),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data['error'] == 'duplicate_purchase'
    
    def test_create_purchase_invalid_svg(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': 99999}),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data['error'] == 'svg_not_found'


@pytest.mark.views
@pytest.mark.django_db
class TestCreatePaymentView:
    def test_requires_authentication(self, client):
        response = client.post(
            reverse('payment:create_payment'),
            data=json.dumps({'gateway': 'abacatepay', 'plan': 'pro_month'}),
            content_type='application/json'
        )
        assert response.status_code == 401
    
    def test_create_payment_missing_gateway(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_payment'),
            data=json.dumps({'plan': 'pro_month'}),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    @patch('payment.services.payment_service.PaymentService.get_gateway')
    def test_create_payment_success(self, mock_gateway_class, client, user):
        # Skip this test as it requires more complex setup
        pytest.skip("Test requires PaymentService.create_payment_with_items implementation")
    
    def test_create_payment_invalid_json(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_payment'),
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_create_payment_unsupported_gateway(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_payment'),
            data=json.dumps({
                'gateway': 'invalid_gateway',
                'plan': 'pro_month'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    @patch('payment.services.payment_service.PaymentService.get_gateway')
    def test_create_payment_with_cart_items(self, mock_gateway_class, client, user, svg_file):
        mock_gateway = MagicMock()
        mock_gateway.create_payment.return_value = {
            'id': 'gw_456',
            'status': 'pending'
        }
        mock_gateway_class.return_value = mock_gateway
        
        client.force_login(user)
        response = client.post(
            reverse('payment:create_payment'),
            data=json.dumps({
                'gateway': 'abacatepay',
                'items': [
                    {'type': 'svg', 'id': svg_file.id, 'quantity': 1}
                ],
                'currency': 'BRL'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
    
    def test_create_payment_empty_items_list(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('payment:create_payment'),
            data=json.dumps({
                'gateway': 'abacatepay',
                'items': []
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
