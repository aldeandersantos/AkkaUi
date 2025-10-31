from django.db import models
from django.conf import settings


class FileAsset(models.Model):
    """
    Modelo simples para armazenar arquivos privados protegidos.
    O caminho do arquivo é relativo ao MEDIA_ROOT.
    """
    name = models.CharField(max_length=255, help_text="Nome descritivo do arquivo")
    file_path = models.CharField(max_length=500, help_text="Caminho relativo ao MEDIA_ROOT")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_assets',
    )
    
    def __str__(self):
        return f"{self.name} - {self.file_path}"
    
    class Meta:
        verbose_name = "Arquivo Protegido"
        verbose_name_plural = "Arquivos Protegidos"
