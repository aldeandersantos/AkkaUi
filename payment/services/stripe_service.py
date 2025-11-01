from djstripe.models import Customer
from usuario.models import CustomUser
import logging

logger = logging.getLogger(__name__)


def get_or_create_stripe_customer(user: CustomUser) -> Customer:
    """
    Obtém ou cria um Customer do Stripe para o usuário.
    
    Args:
        user: Instância de CustomUser
        
    Returns:
        Customer: Objeto Customer do dj-stripe associado ao usuário
    """
    try:
        customer, created = Customer.get_or_create(subscriber=user)
        
        if created:
            logger.info(f"Customer Stripe criado para o usuário {user.username}")
        else:
            logger.info(f"Customer Stripe já existe para o usuário {user.username}")
        
        return customer
    
    except Exception as e:
        logger.error(f"Erro ao criar/obter Customer Stripe para {user.username}: {e}", exc_info=True)
        raise


def sync_user_to_stripe(user: CustomUser) -> Customer:
    """
    Sincroniza dados do usuário com o Stripe Customer.
    Atualiza informações como email e nome no Stripe.
    
    Args:
        user: Instância de CustomUser
        
    Returns:
        Customer: Objeto Customer do dj-stripe atualizado
    """
    try:
        customer = get_or_create_stripe_customer(user)
        
        # Atualizar informações do customer no Stripe se necessário
        update_data = {}
        
        if user.email and customer.email != user.email:
            update_data['email'] = user.email
        
        name = f"{user.first_name} {user.last_name}".strip()
        if name and customer.name != name:
            update_data['name'] = name
        
        if update_data:
            customer.api_retrieve().modify(**update_data)
            customer.refresh_from_db()
            logger.info(f"Customer Stripe atualizado para {user.username}: {update_data}")
        
        return customer
    
    except Exception as e:
        logger.error(f"Erro ao sincronizar usuário {user.username} com Stripe: {e}", exc_info=True)
        raise
