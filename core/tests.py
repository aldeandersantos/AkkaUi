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
        self.assertContains(response, 'Explorar Componentes')
        self.assertContains(response, 'Buttons')
    
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
