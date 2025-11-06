from ..models import Payment
from .payment_service import PaymentService

def processing_stripe_payment(data):
    metadata = data.get("data", {}).get("object", {}).get("metadata", {})
    transaction_id = metadata.get("transaction_id")
    user_email = data.get("data", {}).get("object", {}).get("customer_email")
    return processing_payment(transaction_id, user_email)

def processing_payment(transaction_id: str, user_email: str) -> bool:
    try:
        payment_obj = Payment.objects.get(transaction_id=transaction_id, user__email=user_email)
    except Payment.DoesNotExist:
        return False

    if payment_obj.status == "completed":
        return True

    payment_obj.status = "completed"
    PaymentService._finalize_payment(payment_obj)
    payment_obj.save()
    return True
