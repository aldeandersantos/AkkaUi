

import logging
from django.conf import settings
import stripe

# Função para buscar dados do Stripe
def get_stripe_payment_data(session_id):
    data = {
        'stripe_available': False,
        'payment_status': None,
        'amount': None,
        'currency': None,
    }
    if not session_id:
        return data
    try:
        stripe.api_key = (
            settings.STRIPE_LIVE_SECRET_KEY
            if getattr(settings, 'STRIPE_LIVE_MODE', False)
            else getattr(settings, 'STRIPE_TEST_SECRET_KEY', None)
        )
        session = stripe.checkout.Session.retrieve(session_id)
        data['stripe_available'] = True
        amount_total = getattr(session, 'amount_total', None)
        if amount_total is None and isinstance(session, dict):
            amount_total = session.get('amount_total')
        currency = getattr(session, 'currency', None)
        if currency is None and isinstance(session, dict):
            currency = session.get('currency')
        data['amount'] = (amount_total / 100) if amount_total else None
        data['currency'] = currency.upper() if currency else None
        status = getattr(session, 'status', None)
        if status is None and isinstance(session, dict):
            status = session.get('status')
        status_map = {
            'complete': 'completed',
            'open': 'pending',
            'expired': 'cancelled',
        }
        data['payment_status'] = status_map.get(status, status)
    except Exception as e:
        logging.exception('Erro ao recuperar Checkout Session do Stripe: %s', e)
        data['stripe_error'] = str(e)
    return data




