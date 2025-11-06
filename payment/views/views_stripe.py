
import logging
import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import get_language

logger = logging.getLogger(__name__)
import stripe






# --- PÁGINAS DE SUCESSO E CANCELAMENTO DO CHECKOUT STRIPE ---
class SuccessView(TemplateView):
	"""Página de sucesso do checkout Stripe."""
	template_name = "core/success.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		request = self.request
		session_id = (
			request.GET.get('session_id')
			or request.GET.get('checkout_session_id')
			or request.GET.get('session')
			or request.GET.get('id')
		)
		context['session_id'] = session_id
		context['stripe_available'] = False
		context['payment_status'] = None
		context['amount'] = None
		context['currency'] = None
		try:
			stripe.api_key = (
				settings.STRIPE_LIVE_SECRET_KEY
				if getattr(settings, 'STRIPE_LIVE_MODE', False)
				else getattr(settings, 'STRIPE_TEST_SECRET_KEY', None)
			)
		except Exception:
			logger.debug('Config Stripe não encontrada nas settings')
		try:
			session = stripe.checkout.Session.retrieve(session_id)
			context['stripe_available'] = True
			amount_total = getattr(session, 'amount_total', None)
			if amount_total is None and isinstance(session, dict):
				amount_total = session.get('amount_total')
			currency = getattr(session, 'currency', None)
			if currency is None and isinstance(session, dict):
				currency = session.get('currency')
			context['amount'] = (amount_total / 100) if amount_total else None
			context['currency'] = currency.upper() if currency else None
			status = getattr(session, 'status', None)
			if status is None and isinstance(session, dict):
				status = session.get('status')
			status_map = {
				'complete': 'completed',
				'open': 'pending',
				'expired': 'cancelled',
			}
			context['payment_status'] = status_map.get(status, status)
		except Exception as e:
			logger.exception('Erro ao recuperar Checkout Session do Stripe: %s', e)
			context['stripe_error'] = str(e)
		return context



class CancelView(TemplateView):
	"""Página de cancelamento do checkout."""
	template_name = "core/cancel.html"



