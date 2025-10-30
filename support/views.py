from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Ticket, TicketMessage
from django.template.loader import render_to_string
import json

# Segurança: validação de imagens
from PIL import Image, UnidentifiedImageError
import io
from django.core.files.uploadedfile import InMemoryUploadedFile


@login_required
def ticket_list(request):
    """Lista todos os tickets do usuário logado"""
    if request.user.admin:
        tickets = Ticket.objects.all()
        is_admin_view = True
    else:
        tickets = Ticket.objects.filter(user=request.user)
        is_admin_view = False
    
    context = {
        'tickets': tickets,
        'is_admin_view': is_admin_view
    }
    return render(request, 'support/ticket_list.html', context)


@login_required
def ticket_create(request):
    """Cria um novo ticket"""
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        if not subject or not message_text:
            messages.error(request, 'Assunto e mensagem são obrigatórios.')
            return render(request, 'support/ticket_create.html')
        
        ticket = Ticket.objects.create(
            user=request.user,
            subject=subject
        )
        
        TicketMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=message_text,
            is_staff_reply=False
        )
        
        messages.success(request, f'Ticket #{ticket.id} criado com sucesso!')
        return redirect('support:ticket_detail', ticket_id=ticket.id)
    
    return render(request, 'support/ticket_create.html')


@login_required
def ticket_detail(request, ticket_id):
    """Exibe detalhes de um ticket com todas as mensagens"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if not request.user.admin and ticket.user != request.user:
        messages.error(request, 'Você não tem permissão para ver este ticket.')
        return redirect('support:ticket_list')
    
    ticket_messages = ticket.messages.all()
    
    context = {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
        'can_reply': True
    }
    return render(request, 'support/ticket_detail.html', context)


@login_required
@require_POST
def ticket_reply(request, ticket_id):
    """Adiciona uma mensagem a um ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if not request.user.admin and ticket.user != request.user:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    message_text = request.POST.get('message', '').strip()
    
    if not message_text and 'attachment' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Mensagem vazia'}, status=400)
    
    is_staff = request.user.admin

    # Se o usuário não for staff e tentou enviar um anexo, verifique permissão
    attachment = request.FILES.get('attachment')
    if attachment and not is_staff and not ticket.allow_client_uploads:
        return JsonResponse({'success': False, 'error': 'Uploads de cliente não permitidos neste ticket'}, status=403)

    # Validar tipo de arquivo simples (png/jpg) e sanitizar imagem com Pillow
    if attachment:
        content_type = attachment.content_type
        if content_type not in ('image/png', 'image/jpeg'):
            return JsonResponse({'success': False, 'error': 'Apenas arquivos PNG ou JPG são permitidos'}, status=400)
        # Limite de tamanho (ex: 5 MB)
        max_size = 5 * 1024 * 1024
        if attachment.size > max_size:
            return JsonResponse({'success': False, 'error': 'Arquivo muito grande (máx. 5 MB)'}, status=400)

        # Verifica se o arquivo é realmente uma imagem válida e re-salva para sanitizar metadata
        try:
            attachment.seek(0)
            img = Image.open(attachment)
            img.verify()  # checa integridade básica
        except Exception:
            return JsonResponse({'success': False, 'error': 'Arquivo inválido. Envie uma imagem PNG ou JPG válida.'}, status=400)

        # Reabrir e re-salvar para sanitizar e normalizar formato
        try:
            attachment.seek(0)
            img = Image.open(attachment)
            fmt = (img.format or 'PNG').upper()
            out = io.BytesIO()
            if fmt in ('JPEG', 'JPG'):
                img = img.convert('RGB')
                img.save(out, format='JPEG', quality=85)
                cleaned_content_type = 'image/jpeg'
                ext = 'jpg'
            else:
                img.save(out, format='PNG', optimize=True)
                cleaned_content_type = 'image/png'
                ext = 'png'
            out.seek(0)
            # Nome do arquivo: prefixar para evitar nomes suspeitos
            original_name = getattr(attachment, 'name', 'attachment')
            cleaned_name = f"ticket_{ticket.id}_{original_name}"
            cleaned_file = InMemoryUploadedFile(out, 'attachment', cleaned_name, cleaned_content_type, out.getbuffer().nbytes, None)
            attachment = cleaned_file
        except Exception:
            return JsonResponse({'success': False, 'error': 'Falha ao processar imagem enviada.'}, status=400)

    TicketMessage.objects.create(
        ticket=ticket,
        user=request.user,
        message=message_text,
        is_staff_reply=is_staff,
        attachment=attachment if attachment else None
    )
    
    # Atualiza status se necessário
    if ticket.status == 'closed':
        ticket.status = 'in_progress'
        ticket.save()

    # Se for requisição HTMX, renderiza o partial da nova mensagem e retorna para ser anexado
    if request.headers.get('HX-Request') == 'true':
        # Obter a última mensagem criada (assumindo que ordering é por created_at)
        last_msg = ticket.messages.last()
        html = render_to_string('support/_ticket_message.html', {'msg': last_msg}, request=request)
        # Script para resetar o formulário e rolar até a nova mensagem
        html += "<script>var f=document.getElementById('replyForm'); if(f){f.reset();} var c=document.getElementById('messagesList'); if(c && c.lastElementChild){c.lastElementChild.scrollIntoView({behavior:'smooth'});} </script>"
        return HttpResponse(html)

    messages.success(request, 'Mensagem enviada com sucesso!')
    return redirect('support:ticket_detail', ticket_id=ticket.id)


@login_required
@require_POST
def ticket_update_status(request, ticket_id):
    """Atualiza o status de um ticket (apenas admins)"""
    if not request.user.admin:
        return JsonResponse({'success': False, 'error': 'Apenas admins'}, status=403)
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Ticket.STATUS_CHOICES):
        ticket.status = new_status
        ticket.save()
        messages.success(request, f'Status do ticket atualizado para {ticket.get_status_display()}')
    
    return redirect('support:ticket_detail', ticket_id=ticket.id)


@login_required
@require_POST
def ticket_toggle_client_uploads(request, ticket_id):
    """Ativa/desativa allow_client_uploads em um ticket (apenas admins)."""
    if not request.user.admin:
        return JsonResponse({'success': False, 'error': 'Apenas admins'}, status=403)

    ticket = get_object_or_404(Ticket, id=ticket_id)
    # Toggle boolean
    ticket.allow_client_uploads = not ticket.allow_client_uploads
    ticket.save()

    # Se for requisição HTMX, retornar apenas o fragmento do botão para substituir no DOM
    if request.headers.get('HX-Request') == 'true':
        html = render_to_string('support/_toggle_uploads_button.html', {'ticket': ticket, 'user': request.user}, request=request)
        return HttpResponse(html)

    messages.success(request, f"Uploads do cliente {'ativados' if ticket.allow_client_uploads else 'desativados'} para o ticket #{ticket.id}.")
    return redirect('support:ticket_detail', ticket_id=ticket.id)
