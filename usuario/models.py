from django.db import models
from django.contrib.auth.models import AbstractUser
import secrets
import hashlib
import time

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds phone field (optional) and admin field to control access to admin features.
    """
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Telefone",
        help_text="Telefone de contato (opcional)"
    )
    admin = models.BooleanField(
        default=False,
        verbose_name="Administrador",
        help_text="Permite acesso ao sistema de gerenciamento de SVGs"
    )
    is_active = models.BooleanField(default=True)
    is_vip = models.BooleanField(default=False)
    vip_expiration = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Expiração VIP",
        help_text="Data de expiração do status VIP"
    )
    stripe_customer_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="ID Cliente Stripe",
        help_text="ID do cliente no Stripe para cobrança recorrente"
    )
    stripe_subscription_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="ID Assinatura Stripe",
        help_text="ID da assinatura do Stripe"
    )
    hash_id = models.CharField(max_length=64, blank=True, null=True, unique=True)

    def save(self, *args, **kwargs) -> None:
        # Gera hash único apenas na criação do usuário, preservando em atualizações
        if not self.pk and not self.hash_id:
            try:
                # token_hex(32) gera 64 caracteres hexadecimais
                self.hash_id = secrets.token_hex(32)
            except Exception:
                # fallback seguro caso ocorra algum erro inesperado
                self.hash_id = hashlib.sha256(f"{self.username}-{time.time()}".encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"


class Favorite(models.Model):
    """
    Modelo para armazenar os SVGs favoritos de cada usuário.
    Usa JSONField para armazenar os IDs dos SVGs favoritos.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="Usuário"
    )
    svg_ids = models.JSONField(
        default=list,
        verbose_name="IDs dos SVGs favoritos",
        help_text="Lista de IDs dos SVGs marcados como favoritos"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Favoritos de {self.user.username}"

    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"
