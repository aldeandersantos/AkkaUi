import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from core.utils.date_utils import datefield_now, one_month_more, one_year_more
from ..models import Payment, PaymentItem
from ..gateways import PaymentGateway
from ..gateways.abacate_gateway import AbacatePayGateway
from ..gateways.mercadopago_gateway import MercadoPagoGateway
from ..gateways.stripe_gateway import StripeGateway
from message.views import notify_discord

logger = logging.getLogger(__name__)


class PaymentService:
    """Serviço para gerenciar pagamentos independente do gateway"""
    
    GATEWAY_MAP = {
        'abacatepay': AbacatePayGateway,
        'mercadopago': MercadoPagoGateway,
        'stripe': StripeGateway,
    }
    
    PLAN_PRICES = {
        'pro_month': 9.90,
        'pro_year': 99.90,  # preço anual definido: 99.90
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
            
            # Para AbacatePay, manter status como 'pending' até webhook confirmar
            # Para outros gateways, usar status retornado
            if gateway_name == 'abacatepay':
                payment.status = 'pending'  # Aguardando pagamento PIX
            else:
                payment.status = 'processing' if gateway_response.get('status') != 'failed' else 'failed'
            
            payment.save()
            
            return payment
            
        except Exception as e:
            logger.error(f"Erro ao criar pagamento no gateway {gateway_name}: {type(e).__name__}: {e}", exc_info=True)
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
            
            # Se foi completado agora, executar ações finais (VIP, registro de compras, etc.)
            if payment.status == 'completed' and old_status != 'completed':
                notify_discord(payment.user.username, "confirmed_payment", payment.amount, payment.status)
                # Encapsula ações que devem ocorrer quando um pagamento é confirmado
                cls._finalize_payment(payment, old_status=old_status)
            
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
            
            old_status = payment.status
            payment.status = 'completed'
            payment.gateway_response = confirmation_response
            # Encapsula ações que devem ocorrer quando um pagamento é confirmado
            payment.save()
            cls._finalize_payment(payment, old_status=old_status)
            
            return payment
            
        except Exception as e:
            logger.error(f"Erro ao simular confirmação: {e}")
            payment.error_message = str(e)
            payment.save()
            raise
    
    @classmethod
    def create_payment_with_items(cls, user, gateway_name: str, items: List[Dict[str, Any]], currency: str = 'BRL') -> Payment:
        """
        Cria um novo pagamento com múltiplos itens (carrinho)
        
        Args:
            user: Usuário fazendo o pagamento
            gateway_name: Nome do gateway (abacatepay, mercadopago, paypal)
            items: Lista de dicionários com itens do carrinho
                   Formato: [{'type': 'plan'/'svg', 'id': int/str, 'quantity': int}]
            currency: Moeda (padrão: BRL)
            
        Returns:
            Instância de Payment criada com os itens associados
        """
        from core.models import SvgFile
        
        if gateway_name not in cls.GATEWAY_MAP:
            raise ValueError(f"Gateway não suportado: {gateway_name}")
        
        if not items:
            raise ValueError("Lista de itens não pode estar vazia")
        
        total_amount = Decimal('0.00')
        processed_items = []
        
        # Processar cada item e calcular o total
        for item_data in items:
            item_type = item_data.get('type')
            item_id = item_data.get('id')
            quantity = item_data.get('quantity', 1)
            
            if item_type == 'plan':
                # Item de plano
                price = Decimal(str(cls.get_plan_price(item_id)))
                processed_items.append({
                    'type': 'plan',
                    'id': 0,  # plans não têm ID numérico
                    'name': item_id,
                    'quantity': 1,  # Planos sempre quantidade 1
                    'unit_price': price,
                    'metadata': {'plan_name': item_id}
                })
                total_amount += price
            elif item_type == 'svg':
                # Item SVG
                try:
                    svg = SvgFile.objects.get(id=item_id)
                    if svg.price <= 0:
                        raise ValueError(f"SVG {item_id} não está disponível para venda")
                    processed_items.append({
                        'type': 'svg',
                        'id': svg.id,
                        'name': svg.title_name or f"SVG {svg.id}",
                        'quantity': quantity,
                        'unit_price': svg.price,
                        'metadata': {'svg_id': svg.id, 'hash_value': svg.hash_value}
                    })
                    total_amount += svg.price * quantity
                except SvgFile.DoesNotExist:
                    raise ValueError(f"SVG {item_id} não encontrado")
            else:
                raise ValueError(f"Tipo de item inválido: {item_type}")
        
        # Criar pagamento e itens em uma transação
        with transaction.atomic():
            payment = Payment.objects.create(
                user=user,
                gateway=gateway_name,
                plan=None,  # Não há plano único para carrinho
                amount=total_amount,
                currency=currency,
                status='pending'
            )
            
            # Criar itens do pagamento
            for item_info in processed_items:
                PaymentItem.objects.create(
                    payment=payment,
                    item_type=item_info['type'],
                    item_id=item_info['id'],
                    quantity=item_info['quantity'],
                    unit_price=item_info['unit_price'],
                    item_name=item_info['name'],
                    item_metadata=item_info['metadata']
                )
            
            try:
                # Inicializar gateway e criar pagamento
                gateway = cls.get_gateway(gateway_name)
                # Construir payload de items para enviar ao gateway. Importante:
                # usamos apenas os dados validados/processados pelo servidor
                # (processed_items) e nunca confiamos nos preços/enums vindos do cliente.
                gateway_items = []
                for it in processed_items:
                    gateway_items.append({
                        'id': it.get('id'),
                        'title': it.get('name'),
                        'quantity': int(it.get('quantity', 1)),
                        'currency_id': currency,
                        'unit_price': float(it.get('unit_price')),
                    })

                gateway = cls.get_gateway(gateway_name)
                gateway_response = gateway.create_payment(
                    amount=float(total_amount),
                    currency=currency,
                    metadata={
                        'transaction_id': payment.transaction_id,
                        'user_id': user.id,
                        'items_count': len(processed_items),
                        'items': gateway_items,
                    }
                )
                
                # Atualizar registro com resposta do gateway
                payment.gateway_payment_id = gateway_response.get('id')
                payment.gateway_response = gateway_response
                
                if gateway_name == 'abacatepay':
                    payment.status = 'pending'
                else:
                    payment.status = 'processing' if gateway_response.get('status') != 'failed' else 'failed'
                
                payment.save()
                return payment
                
            except Exception as e:
                logger.error(f"Erro ao criar pagamento no gateway {gateway_name}: {type(e).__name__}: {e}", exc_info=True)
                payment.status = 'failed'
                payment.error_message = str(e)
                payment.save()
                raise
    
    @classmethod
    def _apply_vip_to_user(cls, payment: Payment):
        """Aplica status VIP ao usuário baseado no pagamento"""
        user = payment.user
        
        # Verificar se há plano (pagamento único ou item de plano no carrinho)
        has_plan = False
        plan_name = payment.plan
        
        if not plan_name:
            # Verificar nos itens se há algum plano
            plan_items = payment.items.filter(item_type='plan')
            if plan_items.exists():
                has_plan = True
                plan_name = plan_items.first().item_name
        else:
            has_plan = True
        
        if has_plan:
            user.is_vip = True
            
            # Determinar data de expiração
            if not user.vip_expiration:
                expiration_date = datefield_now()
            else:
                expiration_date = user.vip_expiration
            
            # Adicionar tempo baseado no plano
            if 'year' in plan_name:
                user.vip_expiration = one_year_more(expiration_date)
            else:
                user.vip_expiration = one_month_more(expiration_date)
            
            user.save()
            logger.info(f"VIP aplicado ao usuário {user.username} até {user.vip_expiration}")
        else:
            # Pagamento apenas de SVGs, não aplica VIP
            logger.info(f"Pagamento {payment.transaction_id} sem plano, VIP não aplicado")

    @classmethod
    def _finalize_payment(cls, payment: Payment, old_status: str = None) -> None:
        """Executa ações que devem ocorrer quando um pagamento é confirmado.

        - Marca completed_at
        - Registra compras de SVGs (PaymentItem.item_type == 'svg')
        - Aplica VIP quando aplicável
        - Notifica e registra eventos
        """
        try:
            payment.completed_at = timezone.now()
            # Registrar compras de SVGs associadas aos itens do pagamento
            try:
                cls._register_svg_purchases(payment)
            except Exception as e:
                logger.exception("Falha ao registrar compras de SVGs para pagamento %s: %s", payment.transaction_id, e)

            # Aplicar VIP caso haja plano
            try:
                cls._apply_vip_to_user(payment)
            except Exception as e:
                logger.exception("Falha ao aplicar VIP para pagamento %s: %s", payment.transaction_id, e)

            payment.save()
            logger.info(f"Finalização de pagamento realizada para {payment.transaction_id}")
        except Exception as e:
            logger.exception("Erro ao finalizar pagamento %s: %s", payment.transaction_id, e)

    @classmethod
    def _register_svg_purchases(cls, payment: Payment) -> None:
        """Cria registros Purchase para cada item do tipo 'svg' em um pagamento.

        Observações:
        - Se o usuário já possui o registro de compra para um SVG (unique_together), apenas ignora.
        - Usa get_or_create para evitar duplicação em retries de webhook.
        """
        from ..models import Purchase
        from django.db import IntegrityError

        svg_items = payment.items.filter(item_type='svg')
        if not svg_items.exists():
            logger.debug(f"Pagamento {payment.transaction_id} não contém itens de SVG para registrar")
            return

        for item in svg_items:
            svg_id = item.item_id
            try:
                purchase, created = Purchase.objects.get_or_create(
                    user=payment.user,
                    svg_id=svg_id,
                    defaults={
                        'price': item.unit_price,
                        'payment_method': payment.gateway,
                    }
                )
                if created:
                    logger.info(f"Registro de compra criado: user={payment.user.username}, svg={svg_id}, payment={payment.transaction_id}")
                else:
                    logger.debug(f"Registro de compra já existente: user={payment.user.username}, svg={svg_id}")
            except IntegrityError:
                # Em caso de condição de corrida, tentar obter novamente
                try:
                    Purchase.objects.get(user=payment.user, svg_id=svg_id)
                    logger.debug(f"Registro de compra (race) já existe: user={payment.user.username}, svg={svg_id}")
                except Purchase.DoesNotExist:
                    logger.exception("Erro ao criar purchase para user=%s svg=%s", payment.user.username, svg_id)
