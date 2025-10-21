from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import SvgAsset

# Create your tests here.


class SvgAssetModelTest(TestCase):
    """
    Testes para o modelo SvgAsset
    """

    def setUp(self):
        """
        Configuração inicial para os testes
        """
        self.valid_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="blue"/>
        </svg>'''
        
        self.svg_with_script = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="blue"/>
            <script>alert('XSS');</script>
        </svg>'''
        
        self.svg_with_onclick = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="blue" onclick="alert('XSS')"/>
        </svg>'''

    def test_create_svg_asset_with_text(self):
        """
        Testa a criação de um SvgAsset com svg_text
        """
        svg = SvgAsset.objects.create(
            nome="Test SVG",
            svg_text=self.valid_svg,
            descricao="Um SVG de teste"
        )
        
        self.assertEqual(svg.nome, "Test SVG")
        self.assertIn('circle', svg.svg_text)
        self.assertIsNotNone(svg.data_criacao)

    def test_svg_sanitization_removes_script_tags(self):
        """
        Testa se a sanitização remove tags <script>
        """
        svg = SvgAsset.objects.create(
            nome="SVG with Script",
            svg_text=self.svg_with_script
        )
        
        # Verifica se o script tag foi removido (bleach remove a tag mas pode deixar o conteúdo)
        self.assertNotIn('<script>', svg.svg_text.lower())
        self.assertNotIn('</script>', svg.svg_text.lower())
        # Verifica se o conteúdo válido permanece
        self.assertIn('circle', svg.svg_text)

    def test_svg_sanitization_removes_onclick_attribute(self):
        """
        Testa se a sanitização remove atributos perigosos como onclick
        """
        svg = SvgAsset.objects.create(
            nome="SVG with onclick",
            svg_text=self.svg_with_onclick
        )
        
        # Verifica se o onclick foi removido
        self.assertNotIn('onclick', svg.svg_text.lower())
        # Verifica se o circle ainda existe
        self.assertIn('circle', svg.svg_text)

    def test_svg_asset_with_file(self):
        """
        Testa a criação de um SvgAsset com arquivo
        """
        svg_file = SimpleUploadedFile(
            "test.svg",
            self.valid_svg.encode('utf-8'),
            content_type="image/svg+xml"
        )
        
        svg = SvgAsset.objects.create(
            nome="SVG from File",
            svg_file=svg_file
        )
        
        # Verifica se o svg_text foi extraído do arquivo
        self.assertIn('circle', svg.svg_text)
        self.assertTrue(svg.svg_file.name.startswith('svgs/'))

    def test_svg_asset_str_method(self):
        """
        Testa o método __str__ do modelo
        """
        svg = SvgAsset.objects.create(
            nome="Test SVG",
            svg_text=self.valid_svg
        )
        
        self.assertEqual(str(svg), "Test SVG")

    def test_svg_asset_str_method_without_name(self):
        """
        Testa o método __str__ quando não há nome
        """
        svg = SvgAsset.objects.create(
            svg_text=self.valid_svg
        )
        
        self.assertIn("SVG #", str(svg))

    def test_svg_asset_with_tags(self):
        """
        Testa SvgAsset com tags
        """
        svg = SvgAsset.objects.create(
            nome="Tagged SVG",
            svg_text=self.valid_svg,
            tags="icon, blue, circle"
        )
        
        self.assertEqual(svg.tags, "icon, blue, circle")

    def test_svg_asset_auto_now_update(self):
        """
        Testa se data_atualizacao é atualizada automaticamente
        """
        svg = SvgAsset.objects.create(
            nome="Test SVG",
            svg_text=self.valid_svg
        )
        
        original_update_time = svg.data_atualizacao
        
        # Aguarda um pouco e atualiza
        svg.descricao = "Updated description"
        svg.save()
        
        self.assertGreaterEqual(svg.data_atualizacao, original_update_time)

    def test_sanitize_svg_method_directly(self):
        """
        Testa o método sanitize_svg diretamente
        """
        svg = SvgAsset()
        
        # Testa com SVG válido
        sanitized = svg.sanitize_svg(self.valid_svg)
        self.assertIn('circle', sanitized)
        
        # Testa com script
        sanitized = svg.sanitize_svg(self.svg_with_script)
        self.assertNotIn('<script>', sanitized.lower())
        
        # Testa com string vazia
        sanitized = svg.sanitize_svg("")
        self.assertEqual(sanitized, "")
        
        # Testa com None
        sanitized = svg.sanitize_svg(None)
        self.assertEqual(sanitized, "")

    def test_svg_ordering(self):
        """
        Testa se os SVGs são ordenados por data de criação (mais recentes primeiro)
        """
        svg1 = SvgAsset.objects.create(nome="SVG 1", svg_text=self.valid_svg)
        svg2 = SvgAsset.objects.create(nome="SVG 2", svg_text=self.valid_svg)
        
        svgs = list(SvgAsset.objects.all())
        
        # O mais recente deve vir primeiro
        self.assertEqual(svgs[0].nome, "SVG 2")
        self.assertEqual(svgs[1].nome, "SVG 1")
