import pytest
from decimal import Decimal
from core.serializers import SvgFileSerializer
from payment.serializers import PurchasedSvgSerializer
from core.models import SvgFile
from payment.models import Purchase


@pytest.mark.unit
@pytest.mark.django_db
class TestSvgFileSerializer:
    def test_serialize_svg_file(self, svg_file):
        serializer = SvgFileSerializer(svg_file)
        data = serializer.data
        
        assert data['id'] == svg_file.id
        assert data['title_name'] == svg_file.title_name
        assert 'uploaded_at' in data
    
    def test_serializer_fields(self):
        serializer = SvgFileSerializer()
        expected_fields = ['id', 'title_name', 'uploaded_at']
        assert set(serializer.fields.keys()) == set(expected_fields)
    
    def test_read_only_fields(self):
        serializer = SvgFileSerializer()
        assert serializer.fields['id'].read_only is True
        assert serializer.fields['uploaded_at'].read_only is True


@pytest.mark.unit
@pytest.mark.django_db
class TestPurchasedSvgSerializer:
    def test_serialize_purchase(self, purchase):
        serializer = PurchasedSvgSerializer(purchase)
        data = serializer.data
        
        assert data['id'] == purchase.id
        assert data['svg_id'] == purchase.svg.id
        assert data['svg_title'] == purchase.svg.title_name
        assert Decimal(data['price']) == purchase.price
        assert Decimal(data['svg_price']) == purchase.svg.price
    
    def test_serializer_fields(self):
        serializer = PurchasedSvgSerializer()
        expected_fields = ['id', 'svg_id', 'svg_title', 'price', 'svg_price', 'payment_method', 'purchased_at']
        assert set(serializer.fields.keys()) == set(expected_fields)
    
    def test_read_only_fields(self):
        serializer = PurchasedSvgSerializer()
        assert serializer.fields['id'].read_only is True
        assert serializer.fields['purchased_at'].read_only is True
        assert serializer.fields['svg_id'].read_only is True
        assert serializer.fields['svg_title'].read_only is True
