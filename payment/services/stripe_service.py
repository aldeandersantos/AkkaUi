import stripe
import logging




def stripe_signature_verification(signature_valid, sig_header, payload):
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, 
            sig_header=sig_header, 
            secret=signature_valid
        )
        if not event:
            logging.error("Webhook Stripe: Evento inválido após verificação de assinatura.")
            return
    except ValueError as e:
        logging.error("Webhook Stripe: Payload inválido - %s", e)
        return False
    return True