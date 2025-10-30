from django.db import models
from django.conf import settings


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('in_progress', 'Em Andamento'),
        ('closed', 'Fechado'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='Usuário'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Assunto'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='Status'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.user.username})"
    
    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Ticket'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )
    message = models.TextField(
        verbose_name='Mensagem'
    )
    is_staff_reply = models.BooleanField(
        default=False,
        verbose_name='Resposta da equipe'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    def __str__(self):
        return f"Mensagem em Ticket #{self.ticket.id} por {self.user.username}"
    
    class Meta:
        verbose_name = 'Mensagem de Ticket'
        verbose_name_plural = 'Mensagens de Tickets'
        ordering = ['created_at']
