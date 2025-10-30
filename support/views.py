from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Ticket, TicketMessage
import json


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
    
    if not message_text:
        return JsonResponse({'success': False, 'error': 'Mensagem vazia'}, status=400)
    
    is_staff = request.user.admin
    
    TicketMessage.objects.create(
        ticket=ticket,
        user=request.user,
        message=message_text,
        is_staff_reply=is_staff
    )
    
    if ticket.status == 'closed':
        ticket.status = 'in_progress'
        ticket.save()
    
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
