from django.db import models
from django.conf import settings


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
