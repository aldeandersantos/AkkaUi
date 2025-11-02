from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import os
from pathlib import Path


def validate_file_path(value):
    """
    Valida que o caminho do arquivo é relativo e não contém tentativas de
    directory traversal. Usa Path.resolve() para validação robusta.
    """
    if not value:
        raise ValidationError("O caminho do arquivo não pode estar vazio.")
    
    # Normaliza o caminho
    normalized = os.path.normpath(value)
    
    # Verifica se é um caminho absoluto (verificação rápida antes de resolve)
    if os.path.isabs(normalized):
        raise ValidationError("O caminho do arquivo deve ser relativo ao MEDIA_ROOT.")
    
    # Validação principal: verifica se o caminho resolvido está dentro do MEDIA_ROOT
    # Esta validação cobre directory traversal, symlinks e outros ataques
    try:
        media_root = Path(settings.MEDIA_ROOT).resolve()
        full_path = (media_root / normalized).resolve()
        
        # Verifica se o caminho resolvido está dentro do MEDIA_ROOT
        # relative_to lança ValueError se full_path não está dentro de media_root
        full_path.relative_to(media_root)
        
    except ValueError as e:
        # ValueError indica que o caminho está fora do MEDIA_ROOT ou em drive diferente
        raise ValidationError(
            "O caminho do arquivo resolve para fora do MEDIA_ROOT. "
            "Possível tentativa de directory traversal, symlink malicioso ou paths em drives diferentes."
        )
    except OSError as e:
        # OSError para problemas de I/O ou sistema de arquivos
        raise ValidationError(f"Erro ao validar caminho do arquivo: {str(e)}")
    
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
