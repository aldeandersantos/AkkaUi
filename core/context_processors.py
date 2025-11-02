from django.conf import settings


def stripe_prices(request):
    """Injeta os Stripe Price IDs no contexto do template.

    Lê as variáveis STRIPE_PRICE_MONTHLY/QUARTERLY/ANNUAL de settings
    (recomendado: configurá-las via .env em cada ambiente).
    """
    return {
        'stripe_price_monthly': getattr(settings, 'STRIPE_PRICE_MONTHLY', ''),
        'stripe_price_quarterly': getattr(settings, 'STRIPE_PRICE_QUARTERLY', ''),
        'stripe_price_annual': getattr(settings, 'STRIPE_PRICE_ANNUAL', ''),
    }
