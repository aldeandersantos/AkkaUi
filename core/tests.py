from django.test import TestCase, Client
from django.urls import reverse


class PageViewTests(TestCase):
    """Test that all pages load correctly."""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_page_loads(self):
        """Test that home page loads successfully."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bem-vindo ao AkkaUi')
        self.assertContains(response, 'AkkaUi')
    
    def test_explore_page_loads(self):
        """Test that explore page loads successfully."""
        response = self.client.get(reverse('core:explore'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Explorar SVGs')
        self.assertContains(response, 'explore-sidebar')
    
    def test_pricing_page_loads(self):
        """Test that pricing page loads successfully."""
        response = self.client.get(reverse('core:pricing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Planos e Preços')
        self.assertContains(response, 'Free')
        self.assertContains(response, 'Pro')
        self.assertContains(response, 'Enterprise')
    
    def test_faq_page_loads(self):
        """Test that FAQ page loads successfully."""
        response = self.client.get(reverse('core:faq'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perguntas Frequentes')
        self.assertContains(response, 'O que é o AkkaUi?')


class NavigationTests(TestCase):
    """Test navigation between pages."""
    
    def setUp(self):
        self.client = Client()
    
    def test_header_navigation_links(self):
        """Test that header contains navigation links to all pages."""
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, reverse('core:home'))
        self.assertContains(response, reverse('core:explore'))
        self.assertContains(response, reverse('core:pricing'))
        self.assertContains(response, reverse('core:faq'))
    
    def test_footer_contains_links(self):
        """Test that footer contains links to key pages."""
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Produto')
        self.assertContains(response, 'Recursos')
        self.assertContains(response, 'Empresa')


class SearchFilterTests(TestCase):
    """Test search and filter functionality."""
    
    def setUp(self):
        from usuario.models import CustomUser
        from core.models import SvgFile
        
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
        
        # Criar SVGs de teste
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>'
        
        SvgFile.objects.create(
            title_name='Icon Blue',
            description='A blue icon',
            tags='icon, blue',
            category='Icons',
            content=svg_content,
            owner=self.user,
            is_public=True
        )
        
        SvgFile.objects.create(
            title_name='Logo Red',
            description='A red logo',
            tags='logo, red',
            category='Logos',
            content=svg_content,
            owner=self.user,
            is_public=True
        )
    
    def test_search_by_title(self):
        """Test search by title."""
        response = self.client.get(reverse('core:explore'), {'q': 'Icon'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Icon Blue')
        self.assertNotContains(response, 'Logo Red')
    
    def test_filter_by_category(self):
        """Test filter by category."""
        response = self.client.get(reverse('core:explore'), {'category': 'Icons'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Icon Blue')
        self.assertNotContains(response, 'Logo Red')
    
    def test_filter_by_tag(self):
        """Test filter by tag."""
        response = self.client.get(reverse('core:explore'), {'tag': 'logo'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logo Red')
        self.assertNotContains(response, 'Icon Blue')
    
    def test_sort_by_name(self):
        """Test sort by name."""
        response = self.client.get(reverse('core:explore'), {'sort': 'title_name'})
        self.assertEqual(response.status_code, 200)
        # Verificar se a página carregou com sucesso
        self.assertContains(response, 'Icon Blue')
        self.assertContains(response, 'Logo Red')
    
    def test_api_search(self):
        """Test API search endpoint."""
        response = self.client.get(reverse('core:search_svg'), {'q': 'Icon'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title_name'], 'Icon Blue')
