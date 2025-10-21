from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.exceptions import RequestDataTooBig

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
    - Conteúdo esperado em application/json (UTF-8). Também aceitamos fallback
      em text/plain (corpo inteiro vira svg_text) e form-urlencoded/multipart
      com campos filename e svg_text.

    Cria um novo SvgFile. A sanitização é aplicada quando o conteúdo é servido
    para cópia (via get_sanitized_content), preservando o original no banco.
    """
    ctype = request.META.get("CONTENT_TYPE", "").lower()
    body = b""

    payload = None
    decode_errors = None

    # 1) Tenta JSON padrão (UTF-8). Se falhar, tenta utf-8-sig (remove BOM)
    if ctype.startswith("application/json"):
        # Só acessa request.body quando for realmente JSON para evitar
        # RequestDataTooBig em uploads multipart ou outros content-types.
        try:
            body = request.body or b""
        except RequestDataTooBig:
            return HttpResponseBadRequest(
                json.dumps({
                    "error": "payload too large",
                    "detail": "JSON body exceeded DATA_UPLOAD_MAX_MEMORY_SIZE",
                }),
                content_type="application/json",
            )
        try:
            payload = json.loads(body.decode("utf-8"))
        except UnicodeDecodeError as ue:
            decode_errors = f"unicode-decode-error: {ue}"
            try:
                payload = json.loads(body.decode("utf-8-sig"))
            except Exception as je:
                decode_errors += f"; utf-8-sig-fallback: {je}"
        except json.JSONDecodeError as je:
            decode_errors = f"json-decode-error: {je}"

    # 2) Se não for JSON, tenta form-data/urlencoded
    if payload is None and (ctype.startswith("application/x-www-form-urlencoded") or ctype.startswith("multipart/form-data")):
        svg_text = request.POST.get("svg_text")
        filename = request.POST.get("filename") or "unnamed.svg"
        if svg_text:
            asset = SvgFile.objects.create(filename=filename, content=svg_text)
            return JsonResponse({"id": asset.pk, "filename": asset.filename})

    # 3) Se for text/plain, trata o corpo como SVG direto
    if payload is None and ctype.startswith("text/plain"):
        try:
            # Apenas lê o corpo cru se ainda não tivermos lido
            if body:
                raw = body
            else:
                try:
                    raw = request.body or b""
                except RequestDataTooBig:
                    return HttpResponseBadRequest(
                        json.dumps({
                            "error": "payload too large",
                            "detail": "text/plain body exceeded DATA_UPLOAD_MAX_MEMORY_SIZE",
                        }),
                        content_type="application/json",
                    )
            svg_text = raw.decode("utf-8", errors="replace")
        except Exception:
            svg_text = ""
        if svg_text.strip():
            filename = (request.GET.get("filename") or request.POST.get("filename") or "unnamed.svg")
            asset = SvgFile.objects.create(filename=filename, content=svg_text)
            return JsonResponse({"id": asset.pk, "filename": asset.filename})

    # 4) Se conseguimos JSON, valida campos
    if payload is not None:
        svg_text = payload.get("svg_text")
        if not svg_text:
            return HttpResponseBadRequest(
                json.dumps({"error": "svg_text is required"}),
                content_type="application/json",
            )
        filename = payload.get("filename") or "unnamed.svg"
        asset = SvgFile.objects.create(filename=filename, content=svg_text)
        return JsonResponse({"id": asset.pk, "filename": asset.filename})

    # 5) Falha: retorna detalhes para facilitar o debug no frontend
    return HttpResponseBadRequest(
        json.dumps({
            "error": "invalid json",
            "detail": decode_errors or f"unsupported content-type: {ctype or 'unknown'}",
            "length": len(body),
        }),
        content_type="application/json",
    )