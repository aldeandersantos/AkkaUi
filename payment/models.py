from django.db import models
from django.conf import settings
import secrets


class Payment(models.Model):
    GATEWAY_CHOICES = [
        ('abacatepay', 'Abacate Pay'),
        ('mercadopago', 'Mercado Pago'),
        ('stripe', 'Stripe'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]
    
    PLAN_CHOICES = [
        ('pro_month', 'Pro Mensal'),
        ('pro_year', 'Pro Anual'),
        ('enterprise_month', 'Enterprise Mensal'),
        ('enterprise_year', 'Enterprise Anual'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    plan = models.CharField(max_length=30, choices=PLAN_CHOICES, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BRL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # IDs do gateway de pagamento
    gateway_payment_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    transaction_id = models.CharField(max_length=64, unique=True, editable=False)
    
    # Metadados
    gateway_response = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = secrets.token_hex(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan} - {self.gateway} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'


class PaymentItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('plan', 'Plano'),
        ('svg', 'Arquivo SVG'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    item_id = models.IntegerField(help_text="ID do item (plan_id ou svg_id)")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Metadados do item
    item_name = models.CharField(max_length=255)
    item_metadata = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} x{self.quantity} - {self.total_price}"
    
    class Meta:
        verbose_name = 'Item de Pagamento'
        verbose_name_plural = 'Itens de Pagamento'


class Purchase(models.Model):
    """
    Modelo que registra compras de SVGs por usuários.
    Relaciona um usuário com um SVG específico e armazena informações da transação.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name="Usuário"
    )
    svg = models.ForeignKey(
        'core.SvgFile',
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name="SVG"
    )
    purchased_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da compra"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Preço pago"
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Método de pagamento"
    )
    
    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        unique_together = ['user', 'svg']
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.svg.title_name} ({self.purchased_at.strftime('%Y-%m-%d')})"
