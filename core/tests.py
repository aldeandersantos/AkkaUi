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
            content=svg_content,
            owner=self.user,
            is_public=True
        )
        
        SvgFile.objects.create(
            title_name='Logo Red',
            description='A red logo',
            tags='logo, red',
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


class PurchaseModelTests(TestCase):
    """Test Purchase model and user_access_type method."""
    
    def setUp(self):
        from usuario.models import CustomUser
        from core.models import SvgFile
        from payment.models import Purchase
        
        # Criar usuários
        self.user_normal = CustomUser.objects.create_user(
            username='normal_user',
            email='normal@test.com',
            password='test123'
        )
        
        self.user_vip = CustomUser.objects.create_user(
            username='vip_user',
            email='vip@test.com',
            password='test123',
            is_vip=True
        )
        
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>'
        
        # SVG gratuito
        self.svg_free = SvgFile.objects.create(
            title_name='Free SVG',
            content=svg_content,
            owner=self.user_normal,
            is_public=True,
            price=0
        )
        
        # SVG pago
        self.svg_paid = SvgFile.objects.create(
            title_name='Paid SVG',
            content=svg_content,
            owner=self.user_normal,
            is_public=True,
            is_paid=True,
            price=10.00
        )
        
        # Criar compra
        self.purchase = Purchase.objects.create(
            user=self.user_normal,
            svg=self.svg_paid,
            price=10.00
        )
    
    def test_purchase_model_creation(self):
        """Test that Purchase model is created correctly."""
        from payment.models import Purchase
        
        purchase = Purchase.objects.get(user=self.user_normal, svg=self.svg_paid)
        self.assertEqual(purchase.user, self.user_normal)
        self.assertEqual(purchase.svg, self.svg_paid)
        self.assertEqual(purchase.price, 10.00)
    
    def test_purchase_unique_together(self):
        """Test that unique_together constraint works."""
        from payment.models import Purchase
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            Purchase.objects.create(
                user=self.user_normal,
                svg=self.svg_paid,
                price=10.00
            )
    
    def test_user_access_type_anonymous(self):
        """Test access type for anonymous user."""
        from django.contrib.auth.models import AnonymousUser
        
        anon_user = AnonymousUser()
        
        # SVG gratuito deve retornar 'free'
        self.assertEqual(self.svg_free.user_access_type(anon_user), 'free')
        
        # SVG pago deve retornar 'locked'
        self.assertEqual(self.svg_paid.user_access_type(anon_user), 'locked')
    
    def test_user_access_type_normal_user_with_purchase(self):
        """Test access type for normal user with purchase."""
        # Usuário comprou o SVG pago
        self.assertEqual(self.svg_paid.user_access_type(self.user_normal), 'owned')
        
        # SVG gratuito
        self.assertEqual(self.svg_free.user_access_type(self.user_normal), 'free')
    
    def test_user_access_type_vip_user(self):
        """Test access type for VIP user."""
        # VIP tem acesso a SVG pago sem comprar
        self.assertEqual(self.svg_paid.user_access_type(self.user_vip), 'vip')
        
        # SVG gratuito
        self.assertEqual(self.svg_free.user_access_type(self.user_vip), 'free')
    
    def test_user_access_type_normal_user_locked(self):
        """Test access type for normal user without purchase."""
        from usuario.models import CustomUser
        from core.models import SvgFile
        
        # Criar outro usuário que não comprou
        user_no_purchase = CustomUser.objects.create_user(
            username='no_purchase',
            email='nopurchase@test.com',
            password='test123'
        )
        
        # SVG pago deve estar bloqueado
        self.assertEqual(self.svg_paid.user_access_type(user_no_purchase), 'locked')
        
        # SVG gratuito deve estar disponível
        self.assertEqual(self.svg_free.user_access_type(user_no_purchase), 'free')


class MinhabibliotecaViewTests(TestCase):
    """Test minha_biblioteca view."""
    
    def setUp(self):
        from usuario.models import CustomUser
        from core.models import SvgFile
        from payment.models import Purchase
        
        self.client = Client()
        
        # Criar usuários
        self.user_normal = CustomUser.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='test123'
        )
        
        self.user_vip = CustomUser.objects.create_user(
            username='vip',
            email='vip@test.com',
            password='test123',
            is_vip=True
        )
        
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>'
        
        # SVG gratuito
        self.svg_free = SvgFile.objects.create(
            title_name='Free SVG',
            content=svg_content,
            owner=self.user_normal,
            is_public=True,
            is_paid=False,
            price=0
        )
        
        # SVG pago
        self.svg_paid = SvgFile.objects.create(
            title_name='Paid SVG',
            content=svg_content,
            owner=self.user_normal,
            is_public=True,
            is_paid=True,
            price=10.00
        )
        
        # Compra do usuário normal
        Purchase.objects.create(
            user=self.user_normal,
            svg=self.svg_paid,
            price=10.00
        )
    
    def test_minha_biblioteca_requires_login(self):
        """Test that minha_biblioteca requires login."""
        response = self.client.get(reverse('core:minha_biblioteca'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_minha_biblioteca_normal_user(self):
        """Test minha_biblioteca for normal user."""
        self.client.login(username='normal', password='test123')
        response = self.client.get(reverse('core:minha_biblioteca'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Minha Biblioteca')
        self.assertContains(response, 'Free SVG')
        self.assertContains(response, 'Paid SVG')
        self.assertContains(response, 'SVGs Comprados')
    
    def test_minha_biblioteca_vip_user(self):
        """Test minha_biblioteca for VIP user."""
        self.client.login(username='vip', password='test123')
        response = self.client.get(reverse('core:minha_biblioteca'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Minha Biblioteca')
        self.assertContains(response, 'Você é VIP')
        self.assertContains(response, 'Acesso VIP')
        self.assertContains(response, 'Paid SVG')

