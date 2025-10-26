import json
from decimal import Decimal
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from payment.models import Payment, PaymentItem
from payment.services.payment_service import PaymentService
from payment.views.views_payment import create_payment
from core.models import SvgFile


User = get_user_model()


@override_settings(DEBUG=True)
class CartPaymentTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Criar alguns SVGs para teste
        self.svg1 = SvgFile.objects.create(
            title_name='Logo 1',
            content='<svg></svg>',
            owner=self.user,
            price=Decimal('10.00'),
            is_public=True
        )
        
        self.svg2 = SvgFile.objects.create(
            title_name='Icon Set',
            content='<svg></svg>',
            owner=self.user,
            price=Decimal('25.00'),
            is_public=True
        )
    
    def test_create_payment_with_single_plan_legacy_mode(self):
        """Testa criação de pagamento no modo legado (plano único)"""
        payload = {
            'gateway': 'abacatepay',
            'plan': 'pro_month',
            'currency': 'BRL'
        }
        
        with patch('payment.services.payment_service.PaymentService.get_gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.create_payment.return_value = {
                'id': 'gw_test_123',
                'status': 'pending'
            }
            mock_gateway_class.return_value = mock_gateway
            
            request = self.factory.post(
                '/payment/create/',
                data=json.dumps(payload),
                content_type='application/json'
            )
            request.user = self.user
            
            response = create_payment(request)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['payment']['plan'], 'pro_month')
            self.assertEqual(data['payment']['amount'], '9.90')
    
    def test_create_payment_with_cart_single_svg(self):
        """Testa criação de pagamento com carrinho (1 SVG)"""
        payload = {
            'gateway': 'abacatepay',
            'items': [
                {'type': 'svg', 'id': self.svg1.id, 'quantity': 1}
            ],
            'currency': 'BRL'
        }
        
        with patch('payment.services.payment_service.PaymentService.get_gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.create_payment.return_value = {
                'id': 'gw_test_456',
                'status': 'pending'
            }
            mock_gateway_class.return_value = mock_gateway
            
            request = self.factory.post(
                '/payment/create/',
                data=json.dumps(payload),
                content_type='application/json'
            )
            request.user = self.user
            
            response = create_payment(request)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['payment']['amount'], '10.00')
            self.assertIsNone(data['payment']['plan'])
            self.assertEqual(len(data['payment']['items']), 1)
            self.assertEqual(data['payment']['items'][0]['type'], 'svg')
            self.assertEqual(data['payment']['items'][0]['name'], 'Logo 1')
    
    def test_create_payment_with_cart_multiple_items(self):
        """Testa criação de pagamento com carrinho (múltiplos itens)"""
        payload = {
            'gateway': 'abacatepay',
            'items': [
                {'type': 'svg', 'id': self.svg1.id, 'quantity': 2},
                {'type': 'svg', 'id': self.svg2.id, 'quantity': 1},
                {'type': 'plan', 'id': 'pro_month', 'quantity': 1}
            ],
            'currency': 'BRL'
        }
        
        with patch('payment.services.payment_service.PaymentService.get_gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.create_payment.return_value = {
                'id': 'gw_test_789',
                'status': 'pending'
            }
            mock_gateway_class.return_value = mock_gateway
            
            request = self.factory.post(
                '/payment/create/',
                data=json.dumps(payload),
                content_type='application/json'
            )
            request.user = self.user
            
            response = create_payment(request)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'success')
            # 2x10 + 1x25 + 1x9.90 = 54.90
            self.assertEqual(data['payment']['amount'], '54.90')
            self.assertEqual(len(data['payment']['items']), 3)
            
            # Verificar itens no banco
            payment = Payment.objects.get(transaction_id=data['payment']['transaction_id'])
            self.assertEqual(payment.items.count(), 3)
            
            svg1_item = payment.items.get(item_type='svg', item_id=self.svg1.id)
            self.assertEqual(svg1_item.quantity, 2)
            self.assertEqual(svg1_item.unit_price, Decimal('10.00'))
            self.assertEqual(svg1_item.total_price, Decimal('20.00'))
    
    def test_payment_item_total_price_calculation(self):
        """Testa cálculo automático do total_price no PaymentItem"""
        payment = Payment.objects.create(
            user=self.user,
            gateway='abacatepay',
            amount=Decimal('50.00'),
            currency='BRL'
        )
        
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='svg',
            item_id=self.svg1.id,
            quantity=5,
            unit_price=Decimal('10.00'),
            item_name='Test SVG'
        )
        
        item.refresh_from_db()
        self.assertEqual(item.total_price, Decimal('50.00'))
    
    def test_create_payment_with_invalid_svg_id(self):
        """Testa erro ao tentar comprar SVG inexistente"""
        payload = {
            'gateway': 'abacatepay',
            'items': [
                {'type': 'svg', 'id': 99999, 'quantity': 1}
            ]
        }
        
        request = self.factory.post(
            '/payment/create/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        request.user = self.user
        
        response = create_payment(request)
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('99999', data['error'])
    
    def test_create_payment_with_free_svg(self):
        """Testa erro ao tentar comprar SVG gratuito (preço = 0)"""
        free_svg = SvgFile.objects.create(
            title_name='Free SVG',
            content='<svg></svg>',
            owner=self.user,
            price=Decimal('0.00'),
            is_public=True
        )
        
        payload = {
            'gateway': 'abacatepay',
            'items': [
                {'type': 'svg', 'id': free_svg.id, 'quantity': 1}
            ]
        }
        
        request = self.factory.post(
            '/payment/create/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        request.user = self.user
        
        response = create_payment(request)
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.content)
        self.assertIn('não está disponível para venda', data['error'])
    
    def test_create_payment_with_empty_items_list(self):
        """Testa erro ao enviar lista de itens vazia"""
        payload = {
            'gateway': 'abacatepay',
            'items': []
        }
        
        request = self.factory.post(
            '/payment/create/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        request.user = self.user
        
        response = create_payment(request)
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'items_must_be_non_empty_list')
