"""
Template filters para AkkaUi
"""
import base64
from django import template

register = template.Library()


@register.filter(name='base64_encode')
def base64_encode(value):
    """
    Codifica uma string em base64 para usar em data URIs
    Usado para criar previews de SVG seguros (sem execução de scripts)
    """
    if not value:
        return ''
    try:
        return base64.b64encode(value.encode('utf-8')).decode('utf-8')
    except Exception:
        return ''
