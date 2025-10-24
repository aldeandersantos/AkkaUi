import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from core.utils.date_utils import datefield_now, one_month_more, one_year_more
from ..models import Payment
from ..gateways import PaymentGateway
from ..gateways.abacate_gateway import AbacatePayGateway
from ..gateways.mercadopago_gateway import MercadoPagoGateway
from ..gateways.paypal_gateway import PayPalGateway

logger = logging.getLogger(__name__)


class PaymentService:
    """Serviço para gerenciar pagamentos independente do gateway"""
    
    GATEWAY_MAP = {
        'abacatepay': AbacatePayGateway,
        'mercadopago': MercadoPagoGateway,
        'paypal': PayPalGateway,
    }
    
    PLAN_PRICES = {
        'pro_month': 49.00,
        'pro_year': 470.40,  # 20% desconto
        'enterprise_month': 199.00,
        'enterprise_year': 1910.40,  # 20% desconto
    }
    
    # Mapeamento de status dos gateways para status interno
    STATUS_MAP = {
        'completed': 'completed',
        'confirmed': 'completed',
        'paid': 'completed',
        'pending': 'processing',
        'processing': 'processing',
        'failed': 'failed',
        'cancelled': 'cancelled',
        'canceled': 'cancelled',
    }
    
    @classmethod
    def get_gateway(cls, gateway_name: str) -> PaymentGateway:
        """Retorna uma instância do gateway solicitado"""
        gateway_class = cls.GATEWAY_MAP.get(gateway_name)
        if not gateway_class:
            raise ValueError(f"Gateway não suportado: {gateway_name}")
        return gateway_class()
    
    @classmethod
    def get_plan_price(cls, plan: str) -> float:
        """Retorna o preço do plano"""
        price = cls.PLAN_PRICES.get(plan)
        if price is None:
            raise ValueError(f"Plano não encontrado: {plan}")
        return price
    
    @classmethod
    def create_payment(cls, user, gateway_name: str, plan: str, currency: str = 'BRL') -> Payment:
        """
        Cria um novo pagamento
        
        Args:
            user: Usuário fazendo o pagamento
            gateway_name: Nome do gateway (abacatepay, mercadopago, paypal)
            plan: Nome do plano (pro_month, pro_year, etc)
            currency: Moeda (padrão: BRL)
            
        Returns:
            Instância de Payment criada
        """
        # Validar gateway
        if gateway_name not in cls.GATEWAY_MAP:
            raise ValueError(f"Gateway não suportado: {gateway_name}")
        
        # Obter preço do plano
        amount = cls.get_plan_price(plan)
        
        # Criar registro no banco
        payment = Payment.objects.create(
            user=user,
            gateway=gateway_name,
            plan=plan,
            amount=amount,
            currency=currency,
            status='pending'
        )
        
        try:
            # Inicializar gateway e criar pagamento
            gateway = cls.get_gateway(gateway_name)
            gateway_response = gateway.create_payment(
                amount=float(amount),
                currency=currency,
                metadata={
                    'transaction_id': payment.transaction_id,
                    'plan': plan,
                    'user_id': user.id
                }
            )
            
            # Atualizar registro com resposta do gateway
            payment.gateway_payment_id = gateway_response.get('id')
            payment.gateway_response = gateway_response
            payment.status = 'processing' if gateway_response.get('status') != 'failed' else 'failed'
            payment.save()
            
            return payment
            
        except Exception as e:
            logger.error(f"Erro ao criar pagamento: {e}")
            payment.status = 'failed'
            payment.error_message = str(e)
            payment.save()
            raise
    
    @classmethod
    def check_payment_status(cls, payment: Payment) -> Payment:
        """
        Verifica o status atual de um pagamento
        
        Args:
            payment: Instância de Payment
            
        Returns:
            Payment atualizado
        """
        if not payment.gateway_payment_id:
            raise ValueError("Pagamento não possui ID do gateway")
        
        try:
            gateway = cls.get_gateway(payment.gateway)
            status_response = gateway.check_payment_status(payment.gateway_payment_id)
            
            # Atualizar status
            old_status = payment.status
            new_status = status_response.get('status', payment.status)
            
            payment.status = cls.STATUS_MAP.get(new_status.lower(), payment.status)
            payment.gateway_response = status_response
            
            # Se foi completado agora, registrar timestamp
            if payment.status == 'completed' and old_status != 'completed':
                payment.completed_at = timezone.now()
                cls._apply_vip_to_user(payment)
            
            payment.save()
            return payment
            
        except Exception as e:
            logger.error(f"Erro ao verificar status do pagamento: {e}")
            payment.error_message = str(e)
            payment.save()
            raise
    
    @classmethod
    def simulate_payment_confirmation(cls, payment: Payment) -> Payment:
        """
        Simula a confirmação de um pagamento (apenas para testes)
        
        Args:
            payment: Instância de Payment
            
        Returns:
            Payment atualizado
        """
        if not payment.gateway_payment_id:
            raise ValueError("Pagamento não possui ID do gateway")
        
        try:
            gateway = cls.get_gateway(payment.gateway)
            confirmation_response = gateway.simulate_payment_confirmation(payment.gateway_payment_id)
            
            payment.status = 'completed'
            payment.gateway_response = confirmation_response
            payment.completed_at = timezone.now()
            payment.save()
            
            # Aplicar VIP ao usuário
            cls._apply_vip_to_user(payment)
            
            return payment
            
        except Exception as e:
            logger.error(f"Erro ao simular confirmação: {e}")
            payment.error_message = str(e)
            payment.save()
            raise
    
    @classmethod
    def _apply_vip_to_user(cls, payment: Payment):
        """Aplica status VIP ao usuário baseado no pagamento"""
        user = payment.user
        user.is_vip = True
        
        # Determinar data de expiração
        if not user.vip_expiration:
            expiration_date = datefield_now()
        else:
            expiration_date = user.vip_expiration
        
        # Adicionar tempo baseado no plano
        if 'year' in payment.plan:
            user.vip_expiration = one_year_more(expiration_date)
        else:
            user.vip_expiration = one_month_more(expiration_date)
        
        user.save()
        logger.info(f"VIP aplicado ao usuário {user.username} até {user.vip_expiration}")
