from django.test import TestCase, override_settings, RequestFactory

from payment.views import abacate_status
from payment.views import simulate_sale
from unittest.mock import patch, MagicMock


class AbacateStatusViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	def test_abacate_status_without_key(self):
		"""Se não houver chave, a view deve indicar client_configured False."""
		with override_settings(ABACATE_API_KEY=""):
			request = self.factory.get('/payment/abacate-status/')
			response = abacate_status(request)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(response.json().get('client_configured'), False)

	def test_abacate_status_with_key(self):
		"""Se a chave estiver presente, client_configured True."""
		with override_settings(ABACATE_API_KEY="sk_test_fake"):
			request = self.factory.get('/payment/abacate-status/')
			response = abacate_status(request)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(response.json().get('client_configured'), True)

	def test_simulate_sale_missing_amount(self):
		request = self.factory.post('/payment/simulate-sale/', data='{}', content_type='application/json')
		response = simulate_sale(request)
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json().get('error'), 'missing_amount')

	def test_simulate_sale_with_mocked_client(self):
		payload = {"amount": 1500, "currency": "BRL"}
		request = self.factory.post('/payment/simulate-sale/', data='{"amount": 1500, "currency":"BRL"}', content_type='application/json')

		mock_result = {"id": "gw_1", "status": "created"}

		# Patch the client object in payment.views
		with patch('core.payment.views.client') as mock_client:
			mock_client.create_payment = MagicMock(return_value=mock_result)
			response = simulate_sale(request)
			self.assertEqual(response.status_code, 200)
			json_data = response.json()
			self.assertEqual(json_data.get('status'), 'created')
			self.assertEqual(json_data.get('gateway_response'), mock_result)
