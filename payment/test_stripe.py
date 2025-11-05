from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from djstripe.models import Customer, Subscription, Event
from payment.services.stripe_service import get_or_create_stripe_customer, sync_user_to_stripe
from payment.signals import handle_invoice_payment_succeeded, handle_subscription_deleted, handle_subscription_updated
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

User = get_user_model()


class StripeCustomerSyncTestCase(TestCase):
    """
    Testes para sincronização de usuários com Stripe Customer
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('payment.services.stripe_service.Customer.get_or_create')
    def test_get_or_create_stripe_customer(self, mock_get_or_create):
        """Testa criação de Customer para usuário"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_get_or_create.return_value = (mock_customer, True)
        
        customer = get_or_create_stripe_customer(self.user)
        
        mock_get_or_create.assert_called_once_with(subscriber=self.user)
        self.assertEqual(customer.id, 'cus_test123')
    
    @patch('payment.services.stripe_service.Customer.get_or_create')
    def test_sync_user_to_stripe(self, mock_get_or_create):
        """Testa sincronização de dados do usuário com Stripe"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_customer.email = ''
        mock_customer.name = ''
        mock_get_or_create.return_value = (mock_customer, True)
        
        self.user.first_name = 'Test'
        self.user.last_name = 'User'
        self.user.save()
        
        customer = sync_user_to_stripe(self.user)
        
        self.assertIsNotNone(customer)


class StripeWebhookSignalsTestCase(TestCase):
    """
    Testes para handlers de webhooks do Stripe
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='vipuser',
            email='vip@example.com',
            password='testpass123'
        )
    
    @patch('payment.signals.Subscription.objects.get')
    def test_handle_invoice_payment_succeeded(self, mock_sub_get):
        """Testa atualização de status VIP após pagamento bem-sucedido"""
        # Mock do subscription
        mock_subscription = MagicMock()
        mock_subscription.id = 'sub_test123'
        mock_subscription.current_period_end = datetime.now() + timedelta(days=30)
        
        # Mock do customer
        mock_customer = MagicMock()
        mock_customer.subscriber = self.user
        mock_subscription.customer = mock_customer
        
        mock_sub_get.return_value = mock_subscription
        
        # Mock do event
        mock_event = MagicMock()
        mock_event.type = 'invoice.payment_succeeded'
        mock_event.data = {
            'object': {
                'subscription': 'sub_test123'
            }
        }
        
        handle_invoice_payment_succeeded(mock_event)
        
        # Recarregar usuário do banco
        self.user.refresh_from_db()
        
        self.assertTrue(self.user.is_vip)
        self.assertIsNotNone(self.user.vip_expiration)
    
    @patch('payment.signals.Subscription.objects.get')
    def test_handle_subscription_deleted(self, mock_sub_get):
        """Testa remoção de status VIP após cancelamento"""
        # Configurar usuário como VIP
        self.user.is_vip = True
        self.user.vip_expiration = datetime.now().date() + timedelta(days=30)
        self.user.save()
        
        # Mock do subscription
        mock_subscription = MagicMock()
        mock_subscription.id = 'sub_test123'
        
        # Mock do customer
        mock_customer = MagicMock()
        mock_customer.subscriber = self.user
        mock_subscription.customer = mock_customer
        
        mock_sub_get.return_value = mock_subscription
        
        # Mock do event
        mock_event = MagicMock()
        mock_event.type = 'customer.subscription.deleted'
        mock_event.data = {
            'object': {
                'id': 'sub_test123'
            }
        }
        
        handle_subscription_deleted(mock_event)
        
        # Recarregar usuário do banco
        self.user.refresh_from_db()
        
        self.assertFalse(self.user.is_vip)
        self.assertIsNone(self.user.vip_expiration)


class StripeViewsTestCase(TestCase):
    """
    Testes para views do Stripe
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('payment.views.views_stripe.get_or_create_stripe_customer')
    @patch('payment.views.views_stripe.stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_session_create, mock_get_customer):
        """Testa criação de sessão de checkout"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_get_customer.return_value = mock_customer
        
        mock_session = MagicMock()
        mock_session.id = 'cs_test123'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_session_create.return_value = mock_session
        
        response = self.client.post(
            '/payment/stripe/checkout/',
            data=json.dumps({
                'price_id': 'price_test123',
                'success_url': 'http://example.com/success',
                'cancel_url': 'http://example.com/cancel'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('checkout_url', data)
        self.assertIn('session_id', data)
    
    @patch('payment.views.views_stripe.get_or_create_stripe_customer')
    def test_user_subscription_status(self, mock_get_customer):
        """Testa endpoint de status de assinatura"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_get_customer.return_value = mock_customer
        
        response = self.client.get('/pt-br/payment/stripe/subscription-status/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('is_vip', data)
        self.assertIn('vip_expiration', data)
        self.assertIn('subscriptions', data)
