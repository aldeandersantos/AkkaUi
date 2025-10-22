from django.db import models
from django.conf import settings
import re


class SvgFile(models.Model):
    title_name = models.CharField(max_length=255, blank=True)
    # Campo mantido para compatibilidade com esquema existente (migrations
    # antigas esperam `filename` not-null). Mantemos default vazio para não
    # alterar o comportamento das views — objetivo: mínima alteração.
    filename = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Tags separadas por vírgula")
    category = models.CharField(max_length=100, blank=True)
    content = models.TextField(help_text="Conteúdo do arquivo SVG (texto XML)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='svg_files',
    )
    is_public = models.BooleanField(default=False)
    license_required = models.BooleanField(default=False)
    hash_value = models.CharField(max_length=64, unique=True, blank=True)

    def __str__(self):
        return f"{self.title_name} ({self.uploaded_at.isoformat()})"

    def get_sanitized_content(self):
        """
        Placeholder leve de sanitização: atualmente apenas retorna o conteúdo
        armazenado. Implementamos um stub para que as views que chamam
        get_sanitized_content() não quebrem. Em um passo futuro devemos
        substituir por uma sanitização robusta (whitelist de tags/attrs).
        """
        # Como sanitização mínima e segura para um passo rápido, removemos
        # ocorrências de <script>...</script> e event handlers on*.
        content = self.content or ""
        # remove blocos <script>...</script>
        content = re.sub(r"(?is)<script.*?>.*?</script>", "", content)
        # remove atributos onxxx="..." e onxxx='...'
        content = re.sub(r"(?i)\s+on[a-z]+\s*=\s*(\".*?\"|'.*?'|[^\s>]+)", "", content)
        return content

    def _generate_hash(self, extra: str = "") -> str:
        """
        Gera um hash SHA-256 baseado no conteúdo, nome do arquivo, owner e timestamp.
        O argumento `extra` é usado para alterar o input em caso de colisão.
        """
        import hashlib
        from django.utils import timezone

        base = (
            (self.content or "") + "|" + (self.title_name or "") + "|"
            + str(getattr(self.owner, 'id', '')) + "|"
            + timezone.now().isoformat() + "|" + extra
        )
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        # Apenas gerar hash na criação (quando campo vazio)
        if not self.hash_value:
            # Tentar gerar um hash único; em caso de colisão, acrescenta um salt incremental
            from django.db import IntegrityError
            extra = ""
            attempt = 0
            max_attempts = 5
            while True:
                self.hash_value = self._generate_hash(extra=extra)
                try:
                    super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    # Colisão rara: incrementar extra e tentar novamente
                    attempt += 1
                    if attempt >= max_attempts:
                        # Re-raise after algumas tentativas
                        raise
                    extra = str(attempt)
                    # Continue loop to generate new hash and try saving
        else:
            super().save(*args, **kwargs)