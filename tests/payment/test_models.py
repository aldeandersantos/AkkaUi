import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from payment.models import Payment, PaymentItem, Purchase
from core.models import SvgFile

User = get_user_model()


@pytest.mark.models
@pytest.mark.django_db
class TestPaymentModel:
    def test_create_payment(self, user):
        payment = Payment.objects.create(
            user=user,
            gateway='abacatepay',
            plan='pro_month',
            amount=Decimal('9.90'),
            currency='BRL'
        )
        assert payment.user == user
        assert payment.gateway == 'abacatepay'
        assert payment.plan == 'pro_month'
        assert payment.amount == Decimal('9.90')
        assert payment.status == 'pending'
    
    def test_payment_transaction_id_auto_generated(self, user):
        payment = Payment.objects.create(
            user=user,
            gateway='stripe',
            amount=Decimal('10.00')
        )
        assert payment.transaction_id is not None
        assert len(payment.transaction_id) == 64
    
    def test_payment_transaction_id_unique(self, user):
        payment1 = Payment.objects.create(
            user=user,
            gateway='stripe',
            amount=Decimal('10.00')
        )
        payment2 = Payment.objects.create(
            user=user,
            gateway='stripe',
            amount=Decimal('20.00')
        )
        assert payment1.transaction_id != payment2.transaction_id
    
    def test_payment_str_representation(self, payment):
        str_repr = str(payment)
        assert 'testuser' in str_repr
        assert 'pro_month' in str_repr
        assert 'abacatepay' in str_repr
    
    def test_payment_default_status(self, user):
        payment = Payment.objects.create(
            user=user,
            gateway='mercadopago',
            amount=Decimal('5.00')
        )
        assert payment.status == 'pending'
    
    def test_payment_gateway_choices(self, user):
        for gateway in ['abacatepay', 'mercadopago', 'stripe']:
            payment = Payment.objects.create(
                user=user,
                gateway=gateway,
                amount=Decimal('10.00')
            )
            assert payment.gateway == gateway
    
    def test_payment_status_choices(self, user):
        statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        for status in statuses:
            payment = Payment.objects.create(
                user=user,
                gateway='stripe',
                amount=Decimal('10.00'),
                status=status
            )
            assert payment.status == status
    
    def test_payment_metadata_fields(self, user):
        gateway_response = {'id': 'gw_123', 'status': 'success'}
        payment = Payment.objects.create(
            user=user,
            gateway='stripe',
            amount=Decimal('10.00'),
            gateway_payment_id='gw_123',
            gateway_response=gateway_response,
            error_message='Test error'
        )
        assert payment.gateway_payment_id == 'gw_123'
        assert payment.gateway_response == gateway_response
        assert payment.error_message == 'Test error'
    
    def test_payment_timestamps(self, user):
        payment = Payment.objects.create(
            user=user,
            gateway='stripe',
            amount=Decimal('10.00')
        )
        assert payment.created_at is not None
        assert payment.updated_at is not None


@pytest.mark.models
@pytest.mark.django_db
class TestPaymentItemModel:
    def test_create_payment_item(self, payment, svg_file):
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='svg',
            item_id=svg_file.id,
            quantity=1,
            unit_price=Decimal('10.00'),
            item_name='Test SVG'
        )
        assert item.payment == payment
        assert item.item_type == 'svg'
        assert item.quantity == 1
        assert item.unit_price == Decimal('10.00')
    
    def test_payment_item_total_price_calculation(self, payment):
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='plan',
            item_id=1,
            quantity=3,
            unit_price=Decimal('10.00'),
            item_name='Pro Plan'
        )
        assert item.total_price == Decimal('30.00')
    
    def test_payment_item_total_price_auto_calculated_on_save(self, payment):
        item = PaymentItem(
            payment=payment,
            item_type='svg',
            item_id=1,
            quantity=5,
            unit_price=Decimal('7.50'),
            item_name='Test Item'
        )
        item.save()
        assert item.total_price == Decimal('37.50')
    
    def test_payment_item_str_representation(self, payment):
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='svg',
            item_id=1,
            quantity=2,
            unit_price=Decimal('5.00'),
            item_name='Test SVG'
        )
        str_repr = str(item)
        assert 'Test SVG' in str_repr
        assert 'x2' in str_repr
    
    def test_payment_item_metadata(self, payment):
        metadata = {'color': 'blue', 'size': 'large'}
        item = PaymentItem.objects.create(
            payment=payment,
            item_type='svg',
            item_id=1,
            quantity=1,
            unit_price=Decimal('10.00'),
            item_name='SVG with metadata',
            item_metadata=metadata
        )
        assert item.item_metadata == metadata


@pytest.mark.models
@pytest.mark.django_db
class TestPurchaseModel:
    def test_create_purchase(self, user, svg_file):
        purchase = Purchase.objects.create(
            user=user,
            svg=svg_file,
            price=Decimal('10.00'),
            payment_method='credit_card'
        )
        assert purchase.user == user
        assert purchase.svg == svg_file
        assert purchase.price == Decimal('10.00')
        assert purchase.payment_method == 'credit_card'
    
    def test_purchase_unique_together_constraint(self, user, svg_file):
        Purchase.objects.create(
            user=user,
            svg=svg_file,
            price=Decimal('10.00')
        )
        
        with pytest.raises(IntegrityError):
            Purchase.objects.create(
                user=user,
                svg=svg_file,
                price=Decimal('10.00')
            )
    
    def test_purchase_str_representation(self, purchase):
        str_repr = str(purchase)
        assert 'testuser' in str_repr
        assert 'Test SVG' in str_repr
    
    def test_purchase_default_price(self, user, svg_file):
        purchase = Purchase.objects.create(
            user=user,
            svg=svg_file
        )
        assert purchase.price == Decimal('0.00')
    
    def test_purchase_timestamp(self, purchase):
        assert purchase.purchased_at is not None
    
    def test_purchase_ordering(self, user, svg_file, free_svg):
        purchase1 = Purchase.objects.create(
            user=user,
            svg=svg_file,
            price=Decimal('10.00')
        )
        
        purchase2 = Purchase.objects.create(
            user=user,
            svg=free_svg,
            price=Decimal('0.00')
        )
        
        purchases = Purchase.objects.all()
        assert purchases[0] == purchase2
        assert purchases[1] == purchase1
