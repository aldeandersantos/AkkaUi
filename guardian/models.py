from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import os


def validate_file_path(value):
    """
    Valida que o caminho do arquivo é relativo e não contém tentativas de
    directory traversal (.., absolute paths, etc.)
    """
    if not value:
        raise ValidationError("O caminho do arquivo não pode estar vazio.")
    
    # Normaliza o caminho para detectar tentativas de directory traversal
    normalized = os.path.normpath(value)
    
    # Verifica se é um caminho absoluto
    if os.path.isabs(normalized):
        raise ValidationError("O caminho do arquivo deve ser relativo ao MEDIA_ROOT.")
    
    # Verifica se contém .. que poderia escapar do MEDIA_ROOT
    if normalized.startswith('..') or '/..' in normalized or '\\..' in normalized:
        raise ValidationError("O caminho do arquivo não pode conter '..' (directory traversal).")
    
    return normalized


class FileAsset(models.Model):
    """
    Modelo simples para armazenar arquivos privados protegidos.
    O caminho do arquivo é relativo ao MEDIA_ROOT.
    """
    name = models.CharField(max_length=255, help_text="Nome descritivo do arquivo")
    file_path = models.CharField(
        max_length=500,
        help_text="Caminho relativo ao MEDIA_ROOT",
        validators=[validate_file_path]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_assets',
    )
    
    def __str__(self):
        return f"{self.name} - {self.file_path}"
    
    def clean(self):
        """Validação adicional ao nível do modelo"""
        super().clean()
        if self.file_path:
            self.file_path = validate_file_path(self.file_path)
    
    class Meta:
        verbose_name = "Arquivo Protegido"
        verbose_name_plural = "Arquivos Protegidos"
