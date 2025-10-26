from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from payment.models import Purchase
from core.models import SvgFile
import json

User = get_user_model()


class PurchaseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.svg = SvgFile.objects.create(
            title_name='Test SVG',
            content='<svg></svg>',
            owner=self.user,
            is_public=True,
            price=10.00
        )
    
    def test_purchase_creation(self):
        purchase = Purchase.objects.create(
            user=self.user,
            svg=self.svg,
            price=10.00,
            payment_method='credit_card'
        )
        self.assertEqual(purchase.user, self.user)
        self.assertEqual(purchase.svg, self.svg)
        self.assertEqual(purchase.price, 10.00)
    
    def test_purchase_unique_constraint(self):
        # Criar primeira compra
        Purchase.objects.create(
            user=self.user,
            svg=self.svg,
            price=10.00
        )
        
        # Tentar criar compra duplicada deve falhar
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Purchase.objects.create(
                user=self.user,
                svg=self.svg,
                price=10.00
            )


class PurchasedSvgsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.vip_user = User.objects.create_user(username='vipuser', password='testpass123', is_vip=True)
        
        self.svg1 = SvgFile.objects.create(
            title_name='SVG 1',
            content='<svg></svg>',
            owner=self.user,
            is_public=True,
            price=10.00
        )
        self.svg2 = SvgFile.objects.create(
            title_name='SVG 2',
            content='<svg></svg>',
            owner=self.user,
            is_public=True,
            price=15.00
        )
        
        # Criar compra para o usuário
        Purchase.objects.create(user=self.user, svg=self.svg1, price=10.00)
    
    def test_purchased_svgs_page_requires_login(self):
        response = self.client.get(reverse('payment:purchased_svgs'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_purchased_svgs_page_for_regular_user(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('payment:purchased_svgs'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_vip'])
        self.assertEqual(len(response.context['svgfiles']), 1)
    
    def test_purchased_svgs_page_for_vip_user(self):
        self.client.login(username='vipuser', password='testpass123')
        response = self.client.get(reverse('payment:purchased_svgs'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_vip'])
        # VIP deve ver todos os SVGs públicos
        self.assertEqual(len(response.context['svgfiles']), 2)


class CreatePurchaseViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.svg = SvgFile.objects.create(
            title_name='Test SVG',
            content='<svg></svg>',
            owner=self.user,
            is_public=True,
            price=10.00
        )
    
    def test_create_purchase_requires_authentication(self):
        response = self.client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': self.svg.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_create_purchase_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': self.svg.id, 'price': 10.00}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(Purchase.objects.filter(user=self.user, svg=self.svg).count(), 1)
    
    def test_create_purchase_duplicate(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Criar primeira compra
        Purchase.objects.create(user=self.user, svg=self.svg, price=10.00)
        
        # Tentar criar compra duplicada
        response = self.client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': self.svg.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data['error'], 'duplicate_purchase')
    
    def test_create_purchase_invalid_svg(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('payment:create_purchase'),
            data=json.dumps({'svg_id': 99999}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['error'], 'svg_not_found')
