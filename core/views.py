from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.exceptions import RequestDataTooBig
from usuario.views import admin_required

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

@admin_required
def admin_svg(request):
    """
    Admin-only page for managing SVG files.
    Allows admins to create new SVGs with complete information.
    """
    svgfiles = SvgFile.objects.filter(owner=request.user).order_by("-uploaded_at")
    return render(request, "core/admin_svg.html", {"svgfiles": svgfiles})

@admin_required
@require_POST
def admin_create_svg(request):
    """
    Admin-only endpoint to create a new SVG with full metadata.
    Expects JSON or form-data with filename, content, title_name, description, tags, category.
    """
    ctype = request.META.get("CONTENT_TYPE", "").lower()
    
    # Handle JSON requests
    if ctype.startswith("application/json"):
        try:
            body = request.body or b""
        except RequestDataTooBig:
            return HttpResponseBadRequest(
                json.dumps({"error": "payload too large"}),
                content_type="application/json",
            )
        
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponseBadRequest(
                json.dumps({"error": "invalid json"}),
                content_type="application/json",
            )
        
        svg_text = payload.get("svg_text") or payload.get("content")
        filename = payload.get("filename", "unnamed.svg")
        title_name = payload.get("title_name", "")
        description = payload.get("description", "")
        tags = payload.get("tags", "")
        category = payload.get("category", "")
        is_public = payload.get("is_public", False)
        license_required = payload.get("license_required", False)
    
    # Handle form-data requests
    elif ctype.startswith("application/x-www-form-urlencoded") or ctype.startswith("multipart/form-data"):
        svg_text = request.POST.get("svg_text") or request.POST.get("content")
        filename = request.POST.get("filename", "unnamed.svg")
        title_name = request.POST.get("title_name", "")
        description = request.POST.get("description", "")
        tags = request.POST.get("tags", "")
        category = request.POST.get("category", "")
        is_public = request.POST.get("is_public") == "on" or request.POST.get("is_public") == "true"
        license_required = request.POST.get("license_required") == "on" or request.POST.get("license_required") == "true"
    else:
        return HttpResponseBadRequest(
            json.dumps({"error": "unsupported content-type"}),
            content_type="application/json",
        )
    
    if not svg_text:
        return HttpResponseBadRequest(
            json.dumps({"error": "svg_text or content is required"}),
            content_type="application/json",
        )
    
    # Handle thumbnail upload if present
    thumbnail = None
    if request.FILES.get("thumbnail"):
        thumbnail = request.FILES["thumbnail"]
    
    # Create the SvgFile
    svg_file = SvgFile.objects.create(
        filename=filename,
        title_name=title_name,
        description=description,
        tags=tags,
        category=category,
        content=svg_text,
        owner=request.user,
        is_public=is_public,
        license_required=license_required,
        thumbnail=thumbnail,
    )
    
    return JsonResponse({
        "id": svg_file.pk,
        "filename": svg_file.filename,
        "title_name": svg_file.title_name,
        "success": True,
    })