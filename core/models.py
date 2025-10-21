from django.db import models
import re


class SvgFile(models.Model):
    filename = models.CharField(max_length=255)
    content = models.TextField(help_text="Conteúdo do arquivo SVG (texto XML)")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.uploaded_at.isoformat()})"

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