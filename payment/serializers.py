from rest_framework import serializers
from .models import Purchase
from core.models import SvgFile


class PurchasedSvgSerializer(serializers.ModelSerializer):
    svg_id = serializers.IntegerField(source='svg.id', read_only=True)
    svg_title = serializers.CharField(source='svg.title_name', read_only=True)
    svg_price = serializers.DecimalField(source='svg.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Purchase
        fields = ['id', 'svg_id', 'svg_title', 'price', 'svg_price', 'payment_method', 'purchased_at']
        read_only_fields = ['id', 'purchased_at']
