from django.db import models
from django.conf import settings
import secrets


class Payment(models.Model):
    GATEWAY_CHOICES = [
        ('abacatepay', 'Abacate Pay'),
        ('mercadopago', 'Mercado Pago'),
        ('paypal', 'PayPal'),
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
    plan = models.CharField(max_length=30, choices=PLAN_CHOICES)
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
