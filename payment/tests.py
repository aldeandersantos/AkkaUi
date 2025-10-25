from django.test import TestCase, override_settings, RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from payment.views import abacate_status
from payment.views import simulate_sale
from payment.models import Purchase
from core.models import SvgFile
from unittest.mock import patch, MagicMock

User = get_user_model()


class AbacateStatusViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	def test_abacate_status_without_key(self):
		"""Se não houver chave, a view deve indicar client_configured False."""
		with override_settings(ABACATE_API_TEST_KEY=""):
			request = self.factory.get('/payment/abacate-status/')
			response = abacate_status(request)
			self.assertEqual(response.status_code, 200)
			import json
			data = json.loads(response.content)
			self.assertEqual(data.get('client_configured'), False)

	def test_abacate_status_with_key(self):
		"""Se a chave estiver presente, client_configured True."""
		with override_settings(ABACATE_API_TEST_KEY="sk_test_fake"):
			request = self.factory.get('/payment/abacate-status/')
			response = abacate_status(request)
			self.assertEqual(response.status_code, 200)
			import json
			data = json.loads(response.content)
			self.assertEqual(data.get('client_configured'), True)

	def test_simulate_sale_missing_amount(self):
		request = self.factory.post('/payment/simulate-sale/', data='{}', content_type='application/json')
		response = simulate_sale(request)
		self.assertEqual(response.status_code, 400)
		import json
		data = json.loads(response.content)
		self.assertEqual(data.get('error'), 'missing_amount')

	def test_simulate_sale_with_mocked_client(self):
		payload = {"amount": 1500, "currency": "BRL"}
		request = self.factory.post('/payment/simulate-sale/', data='{"amount": 1500, "currency":"BRL"}', content_type='application/json')

		mock_result = {"id": "gw_1", "status": "created"}

		# Patch the client object in payment.views
		with patch('payment.views.client') as mock_client:
			mock_client.create_payment = MagicMock(return_value=mock_result)
			response = simulate_sale(request)
			self.assertEqual(response.status_code, 200)
			import json
			json_data = json.loads(response.content)
			self.assertEqual(json_data.get('status'), 'created')


class PurchaseModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='testuser',
			email='test@test.com',
			password='test123'
		)
		self.svg = SvgFile.objects.create(
			title_name='Test SVG',
			content='<svg></svg>',
			owner=self.user,
			is_public=True
		)
	
	def test_create_purchase(self):
		"""Testa criação de uma compra"""
		purchase = Purchase.objects.create(
			user=self.user,
			svg=self.svg,
			price=10.00,
			payment_method='PIX'
		)
		self.assertEqual(purchase.user, self.user)
		self.assertEqual(purchase.svg, self.svg)
		self.assertEqual(float(purchase.price), 10.00)
		self.assertIsNotNone(purchase.purchased_at)
	
	def test_unique_purchase_constraint(self):
		"""Testa que um usuário não pode comprar o mesmo SVG duas vezes"""
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
		self.user = User.objects.create_user(
			username='testuser',
			email='test@test.com',
			password='test123'
		)
		self.vip_user = User.objects.create_user(
			username='vipuser',
			email='vip@test.com',
			password='test123',
			is_vip=True
		)
		
		# Criar alguns SVGs
		self.svg1 = SvgFile.objects.create(
			title_name='SVG 1',
			content='<svg></svg>',
			owner=self.user,
			is_public=True
		)
		self.svg2 = SvgFile.objects.create(
			title_name='SVG 2',
			content='<svg></svg>',
			owner=self.user,
			is_public=True
		)
	
	def test_purchased_svgs_page_requires_login(self):
		"""Testa que a página de SVGs comprados requer login"""
		response = self.client.get(reverse('payment:purchased_svgs'))
		self.assertEqual(response.status_code, 302)
		# A URL de redirect pode ser /usuario/login/ ou /usuario/signin/
		self.assertTrue('/usuario/' in response.url or '/accounts/' in response.url)
	
	def test_purchased_svgs_page_shows_purchases(self):
		"""Testa que a página mostra os SVGs comprados"""
		self.client.login(username='testuser', password='test123')
		
		# Criar uma compra
		Purchase.objects.create(
			user=self.user,
			svg=self.svg1,
			price=10.00
		)
		
		response = self.client.get(reverse('payment:purchased_svgs'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'SVG 1')
		self.assertNotContains(response, 'SVG 2')
	
	def test_vip_user_sees_all_svgs(self):
		"""Testa que usuário VIP vê todos os SVGs"""
		self.client.login(username='vipuser', password='test123')
		
		response = self.client.get(reverse('payment:purchased_svgs'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'SVG 1')
		self.assertContains(response, 'SVG 2')
		self.assertContains(response, 'VIP')
	
	def test_create_purchase_api(self):
		"""Testa criação de compra via API"""
		self.client.login(username='testuser', password='test123')
		
		import json
		response = self.client.post(
			reverse('payment:create_purchase'),
			data=json.dumps({'svg_id': self.svg1.id, 'price': 10.00, 'payment_method': 'PIX'}),
			content_type='application/json'
		)
		self.assertEqual(response.status_code, 201)
		
		# Verificar que a compra foi criada
		self.assertTrue(Purchase.objects.filter(user=self.user, svg=self.svg1).exists())
	
	def test_prevent_duplicate_purchase(self):
		"""Testa que compras duplicadas são bloqueadas"""
		self.client.login(username='testuser', password='test123')
		
		# Primeira compra
		Purchase.objects.create(
			user=self.user,
			svg=self.svg1,
			price=10.00
		)
		
		# Tentar comprar novamente
		import json
		response = self.client.post(
			reverse('payment:create_purchase'),
			data=json.dumps({'svg_id': self.svg1.id, 'price': 10.00}),
			content_type='application/json'
		)
		self.assertEqual(response.status_code, 409)
		data = json.loads(response.content)
		self.assertIn('duplicate_purchase', data.get('error', ''))
