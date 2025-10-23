from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.exceptions import RequestDataTooBig
from usuario.views import admin_required
from .services import *

from .models import SvgFile

def home(request):
    """
    Home page with introduction to AkkaUi.
    """
    svgfiles = SvgFile.objects.filter(is_public=True).order_by("-uploaded_at")
    print("debug")
    for svg in svgfiles:
        print(f"SVG File: {svg.title_name}, Uploaded at: {svg.uploaded_at}")
    return render(request, "core/home.html", {"svgfiles": svgfiles})

def explore(request):
    """
    Explore page showing all SVG files from database.
    """
    svgfiles = SvgFile.objects.filter(is_public=True).order_by("-uploaded_at")
    return render(request, "core/explore.html", {"svgfiles": svgfiles})

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
    """Recebe vários content-types e cria um SvgFile. Não usa campo `filename`.

    Suporta:
    - application/json: {"svg_text": "...", "title_name": "..."}
    - multipart/form-data ou x-www-form-urlencoded com campo "svg_text"
    - text/plain com corpo inteiro contendo o SVG
    """
    ctype = request.META.get("CONTENT_TYPE", "").lower()
    body = b""
    payload = None
    decode_errors = None
    # owner is required by SvgFile model; only allow creation for authenticated users
    owner = request.user if request.user.is_authenticated else None

    # JSON branch
    if ctype.startswith("application/json"):
        try:
            body = request.body or b""
        except RequestDataTooBig:
            return HttpResponseBadRequest(
                json.dumps({"error": "payload too large", "detail": "JSON body exceeded DATA_UPLOAD_MAX_MEMORY_SIZE"}),
                content_type="application/json",
            )
        try:
            payload = json.loads(body.decode("utf-8"))
        except UnicodeDecodeError:
            try:
                payload = json.loads(body.decode("utf-8-sig"))
            except Exception as e:
                decode_errors = str(e)
        except json.JSONDecodeError as je:
            decode_errors = str(je)

    # form-data / urlencoded
    if payload is None and (ctype.startswith("application/x-www-form-urlencoded") or ctype.startswith("multipart/form-data")):
        svg_text = request.POST.get("svg_text")
        if svg_text:
            if owner is None:
                return HttpResponseBadRequest(json.dumps({"error": "authentication required to save SVG"}), content_type="application/json")
            thumbnail = request.FILES.get('thumbnail') if request.FILES.get('thumbnail') else None
            asset = SvgFile.objects.create(title_name=(request.POST.get('title_name') or ''), content=svg_text, thumbnail=thumbnail, owner=owner)
            return JsonResponse({"id": asset.pk})

    # text/plain
    if payload is None and ctype.startswith("text/plain"):
        try:
            raw = request.body or b""
        except RequestDataTooBig:
            return HttpResponseBadRequest(
                json.dumps({"error": "payload too large", "detail": "text/plain body exceeded DATA_UPLOAD_MAX_MEMORY_SIZE"}),
                content_type="application/json",
            )
        svg_text = raw.decode("utf-8", errors="replace")
        if svg_text.strip():
            if owner is None:
                return HttpResponseBadRequest(json.dumps({"error": "authentication required to save SVG"}), content_type="application/json")
            asset = SvgFile.objects.create(title_name=(request.GET.get('title_name') or ''), content=svg_text, owner=owner)
            return JsonResponse({"id": asset.pk})

    # JSON payload handling
    if payload is not None:
        svg_text = payload.get("svg_text")
        if not svg_text:
            return HttpResponseBadRequest(json.dumps({"error": "svg_text is required"}), content_type="application/json")
        if owner is None:
            return HttpResponseBadRequest(json.dumps({"error": "authentication required to save SVG"}), content_type="application/json")
        title_name = payload.get("title_name") or ""
        asset = SvgFile.objects.create(title_name=title_name, content=svg_text, owner=owner)
        return JsonResponse({"id": asset.pk})

    # fallback error
    return HttpResponseBadRequest(
        json.dumps({"error": "invalid json", "detail": decode_errors or f"unsupported content-type: {ctype or 'unknown'}", "length": len(body)}),
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
def admin_delete_svg(request):
    try:
        if request.method != "DELETE":
            return HttpResponseNotAllowed(["DELETE"])
        svg_file_id = request.GET.get("id") or request.GET.get("pk")
        if not svg_file_id:
            return HttpResponseBadRequest(json.dumps({"error": "id parameter required"}), content_type="application/json")
        success = del_svg_file(svg_file_id)
        if not success:
            return HttpResponseBadRequest(json.dumps({"error": "SVG file not found"}), content_type="application/json")
        return JsonResponse({"success": True})
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({"error": "failed to delete SVG file", "detail": str(e)}), content_type="application/json")


@admin_required
@require_POST
def admin_create_svg(request):
    """
    Admin-only endpoint to create a new SVG with full metadata.
    Expects JSON or form-data with content/title_name, description, tags, category.
    """
    ctype = request.META.get("CONTENT_TYPE", "").lower()

    # JSON
    if ctype.startswith("application/json"):
        try:
            body = request.body or b""
        except RequestDataTooBig:
            return HttpResponseBadRequest(json.dumps({"error": "payload too large"}), content_type="application/json")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponseBadRequest(json.dumps({"error": "invalid json"}), content_type="application/json")

        svg_text = payload.get("svg_text") or payload.get("content")
        title_name = payload.get("title_name") or ""
        description = payload.get("description", "")
        tags = payload.get("tags", "")
        category = payload.get("category", "")
        is_public = payload.get("is_public", False)
        license_required = payload.get("license_required", False)

    # form-data / urlencoded
    elif ctype.startswith("application/x-www-form-urlencoded") or ctype.startswith("multipart/form-data"):
        svg_text = request.POST.get("svg_text") or request.POST.get("content")
        title_name = request.POST.get("title_name") or ""
        description = request.POST.get("description", "")
        tags = request.POST.get("tags", "")
        category = request.POST.get("category", "")
        is_public = request.POST.get("is_public") == "on" or request.POST.get("is_public") == "true"
        license_required = request.POST.get("license_required") == "on" or request.POST.get("license_required") == "true"

    else:
        return HttpResponseBadRequest(json.dumps({"error": "unsupported content-type"}), content_type="application/json")

    if not svg_text:
        return HttpResponseBadRequest(json.dumps({"error": "svg_text or content is required"}), content_type="application/json")

    thumbnail = request.FILES.get("thumbnail") if request.FILES.get("thumbnail") else None

    svg_file = SvgFile.objects.create(
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

    return JsonResponse({"id": svg_file.pk, "title_name": svg_file.title_name, "success": True})