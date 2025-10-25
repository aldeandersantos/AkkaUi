from rest_framework import serializers
from .models import Purchase
from core.models import SvgFile


class PurchasedSvgSerializer(serializers.ModelSerializer):
    """
    Serializer para SVGs comprados, incluindo informações da compra.
    """
    title_name = serializers.CharField(source='svg.title_name', read_only=True)
    description = serializers.CharField(source='svg.description', read_only=True)
    thumbnail = serializers.ImageField(source='svg.thumbnail', read_only=True)
    svg_content = serializers.SerializerMethodField()
    svg_id = serializers.IntegerField(source='svg.id', read_only=True)
    
    class Meta:
        model = Purchase
        fields = ['id', 'svg_id', 'title_name', 'description', 'thumbnail', 
                  'svg_content', 'purchased_at', 'price', 'payment_method']
    
    def get_svg_content(self, obj):
        # Retorna o conteúdo sanitizado do SVG
        return obj.svg.get_sanitized_content() if obj.svg else ""


class SvgWithPurchaseStatusSerializer(serializers.ModelSerializer):
    """
    Serializer para SVGs que inclui status de compra para o usuário atual.
    """
    purchased_by_current_user = serializers.SerializerMethodField()
    
    class Meta:
        model = SvgFile
        fields = ['id', 'title_name', 'description', 'thumbnail', 'category', 
                  'tags', 'uploaded_at', 'purchased_by_current_user']
    
    def get_purchased_by_current_user(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Verifica se o usuário já comprou este SVG
        return Purchase.objects.filter(user=request.user, svg=obj).exists()
