import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse
from abacatepay import AbacatePay
from .services.services_abacate import *


ABACATE_API_TEST_KEY: str = getattr(settings, "ABACATE_API_TEST_KEY", "")


client = AbacatePay(api_key=ABACATE_API_TEST_KEY) if AbacatePay is not None else None


def abacate_status(request):
	"""View simples para verificar se o client do gateway foi configurado.

	Retorna JSON com flag `client_configured` dependendo da presença da chave.
	"""
	return JsonResponse({"client_configured": bool(ABACATE_API_TEST_KEY)})


@csrf_exempt
def simulate_sale(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)


    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    amount = data.get("amount")
    currency = data.get("currency", "BRL")

    if not amount:
        return JsonResponse({"error": "missing_amount"}, status=400)

    if client is not None:
        try:
            payload = {
                "amount": amount,
                "currency": currency,
            }
            result = client.pixQrCode.create(payload)
            gateway_response = norm_response(result)
            return JsonResponse({"status": "created", "gateway_response": gateway_response})
        except Exception as exc:
            return JsonResponse({"status": "error", "detail": str(exc)}, status=502)

    simulated = {"id": "sim_tx_123", "amount": amount, "currency": currency, "status": "created"}
    return JsonResponse({"status": "created", "gateway_response": simulated})


@csrf_exempt
def simulate_confirmation(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    payment_id = data.get("id")
    if not payment_id:
        return JsonResponse({"error": "missing_payment_id"}, status=400)

    status = str(data.get("status"))
    if status != "confirmed":
        return JsonResponse({"error": "invalid_status"}, status=400)

    if client is not None:
        try:
            result = client.pixQrCode.simulate(id=payment_id)
            gateway_response = norm_response(result)
            return JsonResponse({"status": status, "gateway_response": gateway_response})
        except Exception as exc:
            msg = str(exc)
            if "not found" in msg.lower() or "not_found" in msg.lower():
                return JsonResponse({"error": "payment_not_found", "detail": msg}, status=404)
            return JsonResponse({"status": "error", "detail": msg}, status=502)

    simulated_confirmation = {"id": payment_id, "status": status}
    return JsonResponse({"status": status, "gateway_response": simulated_confirmation})

