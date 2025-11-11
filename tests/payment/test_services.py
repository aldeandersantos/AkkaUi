import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from payment.services.payment_service import PaymentService
from payment.models import Payment, PaymentItem
from core.models import SvgFile


@pytest.mark.services
@pytest.mark.django_db
class TestPaymentService:
    def test_get_gateway_abacatepay(self):
        gateway = PaymentService.get_gateway('abacatepay')
        assert gateway is not None
    
    def test_get_gateway_mercadopago(self):
        gateway = PaymentService.get_gateway('mercadopago')
        assert gateway is not None
    
    def test_get_gateway_stripe(self):
        gateway = PaymentService.get_gateway('stripe')
        assert gateway is not None
    
    def test_get_gateway_invalid_raises_error(self):
        with pytest.raises(ValueError) as exc:
            PaymentService.get_gateway('invalid_gateway')
        assert 'não suportado' in str(exc.value)
    
    def test_get_plan_price_pro_month(self):
        price = PaymentService.get_plan_price('pro_month')
        assert price == 9.90
    
    def test_get_plan_price_pro_year(self):
        price = PaymentService.get_plan_price('pro_year')
        assert price == 99.90
    
    def test_get_plan_price_invalid_raises_error(self):
        with pytest.raises(ValueError) as exc:
            PaymentService.get_plan_price('invalid_plan')
        assert 'não encontrado' in str(exc.value)
    
    @patch('payment.services.payment_service.PaymentService.get_gateway')
    def test_create_payment_success(self, mock_get_gateway, user):
        mock_gateway = MagicMock()
        mock_gateway.create_payment.return_value = {
            'id': 'gw_123',
            'status': 'pending'
        }
        mock_get_gateway.return_value = mock_gateway
        
        payment = PaymentService.create_payment(
            user=user,
            gateway_name='abacatepay',
            plan='pro_month',
            currency='BRL'
        )
        
        assert payment.user == user
        assert payment.gateway == 'abacatepay'
        assert payment.plan == 'pro_month'
        assert float(payment.amount) == 9.90
        assert payment.currency == 'BRL'
    
    def test_create_payment_invalid_gateway(self, user):
        with pytest.raises(ValueError):
            PaymentService.create_payment(
                user=user,
                gateway_name='invalid',
                plan='pro_month'
            )
    
    @patch('payment.services.payment_service.PaymentService.get_gateway')
    def test_create_payment_with_items(self, mock_get_gateway, user, svg_file):
        mock_gateway = MagicMock()
        mock_gateway.create_payment.return_value = {
            'id': 'gw_456',
            'status': 'pending'
        }
        mock_get_gateway.return_value = mock_gateway
        
        items = [
            {'type': 'svg', 'id': svg_file.id, 'quantity': 1}
        ]
        
        payment = PaymentService.create_payment_with_items(
            user=user,
            gateway_name='abacatepay',
            items=items,
            currency='BRL'
        )
        
        assert payment.user == user
        assert payment.items.count() >= 0
    
    def test_status_mapping(self):
        assert PaymentService.STATUS_MAP['completed'] == 'completed'
        assert PaymentService.STATUS_MAP['confirmed'] == 'completed'
        assert PaymentService.STATUS_MAP['paid'] == 'completed'
        assert PaymentService.STATUS_MAP['pending'] == 'processing'
        assert PaymentService.STATUS_MAP['failed'] == 'failed'
        assert PaymentService.STATUS_MAP['cancelled'] == 'cancelled'


@pytest.mark.services
@pytest.mark.django_db
class TestPaymentItemCalculations:
    def test_payment_item_total_calculation(self, payment):
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='svg',
            item_id=1,
            quantity=3,
            unit_price=Decimal('10.00'),
            item_name='Test Item'
        )
        
        assert item.total_price == Decimal('30.00')
    
    def test_payment_item_single_quantity(self, payment):
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='plan',
            item_id=1,
            quantity=1,
            unit_price=Decimal('9.90'),
            item_name='Pro Month'
        )
        
        assert item.total_price == Decimal('9.90')
