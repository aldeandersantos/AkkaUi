from django.db import models
from django.contrib.auth.models import AbstractUser

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
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
