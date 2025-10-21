from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import SvgFile

def home(request):
    """
    Home page with introduction to AkkaUi.
    """
    svgfiles = SvgFile.objects.order_by("-uploaded_at")
    return render(request, "core/home.html", {"svgfiles": svgfiles})

def explore(request):
    """
    Explore page showing UI components catalog.
    """
    return render(request, "core/explore.html")

def pricing(request):
    """
    Pricing page showing subscription plans.
    """
    return render(request, "core/pricing.html")

def faq(request):
    """
    FAQ page with frequently asked questions.
    """
    return render(request, "core/faq.html")

def copy_svg(request):
    """
    GET ?id=<pk>
    Retorna JSON {"svg_text": "..."} com o markup sanitizado do campo content.
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    pk = request.GET.get("id") or request.GET.get("pk")
    if not pk:
        return HttpResponseBadRequest(json.dumps({"error": "id query param required"}), content_type="application/json")

    svg = get_object_or_404(SvgFile, pk=pk)
    # Usamos o helper do modelo para obter conteúdo sanitizado
    content = svg.get_sanitized_content()
    return JsonResponse({"svg_text": content})

@csrf_exempt  # remova se quiser exigir CSRF
@require_POST
def paste_svg(request):
    """
    POST JSON: {"filename": "nome.svg", "svg_text": "<svg...>"}
    Cria um novo SvgFile. A sanitização é aplicada quando o conteúdo é servido
    para cópia (via get_sanitized_content), preservando o original no banco.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest(json.dumps({"error": "invalid json"}), content_type="application/json")

    svg_text = payload.get("svg_text")
    if not svg_text:
        return HttpResponseBadRequest(json.dumps({"error": "svg_text is required"}), content_type="application/json")

    filename = payload.get("filename") or "unnamed.svg"
    # Ao criar, o save() sanitizará o conteúdo (conforme models.save override acima)
    asset = SvgFile.objects.create(filename=filename, content=svg_text)
    return JsonResponse({"id": asset.pk, "filename": asset.filename})