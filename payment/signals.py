from django.dispatch import receiver
from djstripe.signals import webhook_post_process
from djstripe.models import Customer, Subscription, Invoice, Event
from usuario.models import CustomUser
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@receiver(webhook_post_process)
def handle_stripe_webhook(sender, event, **kwargs):
    """
    Handler principal para webhooks do Stripe.
    Processa eventos relevantes para gerenciar status VIP de usuários.
    """
    event_type = event.type
    
    try:
        if event_type == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded(event)
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(event)
        elif event_type == 'customer.subscription.updated':
            handle_subscription_updated(event)
    except Exception as e:
        logger.error(f"Erro ao processar webhook {event_type}: {e}", exc_info=True)


def handle_invoice_payment_succeeded(event):
    """
    Processa pagamento bem-sucedido de uma invoice.
    Atualiza is_vip e vip_expiration do usuário.
    """
    invoice_data = event.data.get('object', {})
    subscription_id = invoice_data.get('subscription')
    
    if not subscription_id:
        logger.info("Invoice sem subscription_id, ignorando")
        return
    
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        customer = subscription.customer
        
        if not customer or not customer.subscriber:
            logger.warning(f"Subscription {subscription_id} sem customer ou subscriber válido")
            return
        
        user = customer.subscriber
        
        # Atualizar status VIP
        user.is_vip = True
        
        # Buscar dados atualizados do Stripe
        try:
            stripe_sub = subscription.api_retrieve()
            current_period_end = stripe_sub.get('current_period_end')
        except Exception as e:
            logger.warning(f"Erro ao buscar dados da subscription: {e}")
            # Fallback para dados locais
            stripe_data = getattr(subscription, 'stripe_data', {})
            current_period_end = stripe_data.get('current_period_end')
        
        if current_period_end:
            user.vip_expiration = datetime.fromtimestamp(current_period_end).date()
        
        user.save()
        
        logger.info(f"Usuário {user.username} atualizado para VIP até {user.vip_expiration}")
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} não encontrada")
    except Exception as e:
        logger.error(f"Erro ao processar invoice.payment_succeeded: {e}", exc_info=True)


def handle_subscription_deleted(event):
    """
    Processa cancelamento de assinatura.
    Remove status VIP do usuário.
    """
    subscription_data = event.data.get('object', {})
    subscription_id = subscription_data.get('id')
    
    if not subscription_id:
        return
    
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        customer = subscription.customer
        
        if not customer or not customer.subscriber:
            logger.warning(f"Subscription {subscription_id} sem customer ou subscriber válido")
            return
        
        user = customer.subscriber
        
        # Remover status VIP
        user.is_vip = False
        user.vip_expiration = None
        user.save()
        
        logger.info(f"Status VIP removido do usuário {user.username}")
        
    except Subscription.DoesNotExist:
        logger.warning(f"Subscription {subscription_id} não encontrada no banco local")
    except Exception as e:
        logger.error(f"Erro ao processar customer.subscription.deleted: {e}", exc_info=True)


def handle_subscription_updated(event):
    """
    Processa atualização de assinatura.
    Atualiza status VIP baseado no status da assinatura.
    """
    subscription_data = event.data.get('object', {})
    subscription_id = subscription_data.get('id')
    status = subscription_data.get('status')
    
    if not subscription_id:
        return
    
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        customer = subscription.customer
        
        if not customer or not customer.subscriber:
            logger.warning(f"Subscription {subscription_id} sem customer ou subscriber válido")
            return
        
        user = customer.subscriber
        
        # Atualizar status VIP baseado no status da assinatura
        if status in ['active', 'trialing']:
            user.is_vip = True
            # Buscar dados atualizados do Stripe
            try:
                stripe_sub = subscription.api_retrieve()
                current_period_end = stripe_sub.get('current_period_end')
            except Exception as e:
                logger.warning(f"Erro ao buscar dados da subscription: {e}")
                # Fallback para dados locais
                stripe_data = getattr(subscription, 'stripe_data', {})
                current_period_end = stripe_data.get('current_period_end')
            
            if current_period_end:
                user.vip_expiration = datetime.fromtimestamp(current_period_end).date()
        elif status in ['canceled', 'unpaid', 'incomplete_expired']:
            user.is_vip = False
            user.vip_expiration = None
        
        user.save()
        
        logger.info(f"Usuário {user.username} atualizado - VIP: {user.is_vip}, status subscription: {status}")
        
    except Subscription.DoesNotExist:
        logger.warning(f"Subscription {subscription_id} não encontrada no banco local")
    except Exception as e:
        logger.error(f"Erro ao processar customer.subscription.updated: {e}", exc_info=True)
