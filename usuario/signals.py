from django.db.models.signals import post_save
from django.dispatch import receiver
from djstripe.models import Customer
from .models import CustomUser 
import logging

logger = logging.getLogger(__name__)

# Este sinal é executado sempre que um CustomUser é salvo
@receiver(post_save, sender=CustomUser)
def create_stripe_customer_for_customuser(sender, instance, created, **kwargs):
    """Cria Customer do dj-stripe para novo usuário comum."""
    if created and not instance.is_staff and not instance.is_superuser:
        try:
            customer, created = Customer.get_or_create(subscriber=instance)
            if created:
                logger.info(f"Cliente Stripe criado para: {instance.username}")
        except Exception as e:
            logger.error(f"Erro ao criar Customer Stripe para {instance.username}: {e}", exc_info=True)