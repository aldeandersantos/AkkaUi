from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds phone field (optional) to the default User model.
    """
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Telefone",
        help_text="Telefone de contato (opcional)"
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
