import logging
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.utils.translation import get_language

logger = logging.getLogger(__name__)

try:
	import stripe
	stripe_imported = True
except Exception:
	stripe = None
	stripe_imported = False



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
		if session_id and stripe_imported:
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




@csrf_exempt
@require_POST
def create_checkout_session(request):
	"""Cria uma Stripe Checkout Session e retorna a URL de redirecionamento."""
	try:
		data = json.loads(request.body)
	except Exception:
		return JsonResponse({"error": "invalid_json"}, status=400)

	amount = data.get('amount')
	currency = data.get('currency', 'BRL')
	metadata = data.get('metadata') or {}
	product_name = data.get('product_name', 'Pagamento AkkaUi')
	if not amount:
		return JsonResponse({"error": "missing_amount"}, status=400)

	# Normaliza metadata para string
	stripe_metadata = {}
	for key, value in (metadata.items() if isinstance(metadata, dict) else {}):
		try:
			stripe_metadata[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
		except Exception:
			stripe_metadata[key] = str(value)

	base_url = getattr(settings, 'BASE_URL', None) or 'http://localhost:8000'
	base_url = base_url.rstrip('/')
	lang = get_language() or getattr(settings, 'LANGUAGE_CODE', '')
	lang = lang.strip('/')
	prefix = f"/{lang}" if lang else ''
	success_url = f"{base_url}{prefix}/success/?session_id={{CHECKOUT_SESSION_ID}}"
	cancel_url = f"{base_url}{prefix}/cancel/"

	if stripe_imported:
		try:
			stripe.api_key = (
				settings.STRIPE_LIVE_SECRET_KEY
				if getattr(settings, 'STRIPE_LIVE_MODE', False)
				else getattr(settings, 'STRIPE_TEST_SECRET_KEY', None)
			)
		except Exception:
			logger.debug('Config Stripe não encontrada nas settings')

	try:
		checkout_session = stripe.checkout.Session.create(
			payment_method_types=['card'],
			line_items=[{
				'price_data': {
					'currency': currency.lower(),
					'unit_amount': int(float(amount) * 100),
					'product_data': {'name': product_name},
				},
				'quantity': 1,
			}],
			mode='payment',
			success_url=success_url,
			cancel_url=cancel_url,
			metadata=stripe_metadata,
		)
		return JsonResponse({'id': checkout_session.id, 'url': checkout_session.url})
	except Exception as e:
		logger.exception('Erro criando Checkout Session: %s', e)
		return JsonResponse({"error": "stripe_error", "detail": str(e)}, status=502)

