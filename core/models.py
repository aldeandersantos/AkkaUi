from django.db import models
from django.utils import timezone
import bleach
import re

# Create your models here.





class UiWikiComponent(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField("nome", max_length=255)
    categoria = models.CharField("categoria", max_length=100, blank=True)
    link_figma = models.TextField("link_figma", blank=True)
    autor = models.CharField("autor", max_length=100, blank=True)
    tags = models.TextField("tags", blank=True, help_text="Tags separadas por vírgula")
    thumbnail_url = models.TextField("thumbnail_url", blank=True)
    data_importacao = models.DateTimeField("data_importacao", default=timezone.now)

    class Meta:
        verbose_name = "Componente UIWiki"
        verbose_name_plural = "Componentes UIWiki"
        ordering = ["-data_importacao"]

    def __str__(self):
        return self.nome or f"Componente #{self.pk}"


class SvgAsset(models.Model):
    """
    Modelo para armazenar arquivos SVG.
    Suporta tanto o armazenamento do markup SVG em texto quanto o arquivo.
    """
    id = models.AutoField(primary_key=True)
    nome = models.CharField("nome", max_length=255)
    svg_text = models.TextField("SVG Markup", blank=True, help_text="Código SVG sanitizado")
    svg_file = models.FileField("Arquivo SVG", upload_to='svgs/', blank=True, null=True)
    descricao = models.TextField("descrição", blank=True)
    tags = models.TextField("tags", blank=True, help_text="Tags separadas por vírgula")
    data_criacao = models.DateTimeField("data de criação", default=timezone.now)
    data_atualizacao = models.DateTimeField("última atualização", auto_now=True)

    class Meta:
        verbose_name = "SVG Asset"
        verbose_name_plural = "SVG Assets"
        ordering = ["-data_criacao"]

    def __str__(self):
        return self.nome or f"SVG #{self.pk}"

    def sanitize_svg(self, svg_content):
        """
        Sanitiza o conteúdo SVG removendo scripts e atributos potencialmente perigosos.
        
        Args:
            svg_content (str): O conteúdo SVG a ser sanitizado
            
        Returns:
            str: O conteúdo SVG sanitizado
        """
        if not svg_content:
            return ""
        
        # Remove tags <script> e seu conteúdo
        svg_content = re.sub(r'<script[^>]*>.*?</script>', '', svg_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Lista de tags SVG permitidas
        allowed_tags = [
            'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
            'text', 'tspan', 'tref', 'textPath', 'defs', 'linearGradient', 'radialGradient',
            'stop', 'pattern', 'clipPath', 'mask', 'use', 'symbol', 'marker', 'title', 'desc',
            'metadata', 'foreignObject', 'image', 'animate', 'animateTransform', 'animateMotion',
            'set', 'filter', 'feBlend', 'feColorMatrix', 'feComponentTransfer', 'feComposite',
            'feConvolveMatrix', 'feDiffuseLighting', 'feDisplacementMap', 'feFlood', 'feGaussianBlur',
            'feImage', 'feMerge', 'feMergeNode', 'feMorphology', 'feOffset', 'feSpecularLighting',
            'feTile', 'feTurbulence', 'feDistantLight', 'fePointLight', 'feSpotLight'
        ]
        
        # Lista de atributos perigosos a serem removidos
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout', 
                          'onmousemove', 'onmousedown', 'onmouseup', 'onfocus', 'onblur',
                          'onchange', 'onsubmit', 'onkeydown', 'onkeyup', 'onkeypress']
        
        # Usa bleach para sanitizar
        sanitized = bleach.clean(
            svg_content,
            tags=allowed_tags,
            attributes={
                '*': lambda tag, name, value: name.lower() not in dangerous_attrs
            },
            strip=True
        )
        
        return sanitized

    def save(self, *args, **kwargs):
        """
        Override do método save para sanitizar o SVG antes de salvar.
        """
        # Sanitiza o svg_text se fornecido
        if self.svg_text:
            self.svg_text = self.sanitize_svg(self.svg_text)
        
        # Se um arquivo foi fornecido mas não há svg_text, lê o arquivo
        if self.svg_file and not self.svg_text:
            try:
                self.svg_file.seek(0)
                content = self.svg_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                self.svg_text = self.sanitize_svg(content)
            except Exception:
                pass  # Em caso de erro, mantém o svg_text vazio
        
        super().save(*args, **kwargs)
