from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PaymentGateway(ABC):
    """Classe abstrata base para todos os gateways de pagamento"""
    
    @abstractmethod
    def create_payment(self, amount: float, currency: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cria um pagamento no gateway
        
        Args:
            amount: Valor do pagamento
            currency: Moeda (ex: BRL, USD)
            metadata: Dados adicionais do pagamento
            
        Returns:
            Dict com informações do pagamento criado incluindo:
            - id: ID do pagamento no gateway
            - status: Status do pagamento
            - payment_url: URL para pagamento (se aplicável)
            - qr_code: QR code para pagamento PIX (se aplicável)
        """
        pass
    
    @abstractmethod
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Verifica o status de um pagamento
        
        Args:
            payment_id: ID do pagamento no gateway
            
        Returns:
            Dict com status atualizado do pagamento
        """
        pass
    
    @abstractmethod
    def simulate_payment_confirmation(self, payment_id: str) -> Dict[str, Any]:
        """
        Simula a confirmação de um pagamento (apenas para ambiente de teste)
        
        Args:
            payment_id: ID do pagamento no gateway
            
        Returns:
            Dict com confirmação do pagamento
        """
        pass
    
    @abstractmethod
    def get_gateway_name(self) -> str:
        """Retorna o nome do gateway"""
        pass
