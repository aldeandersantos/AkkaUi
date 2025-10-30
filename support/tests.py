from django.test import TestCase, Client
from django.urls import reverse
from usuario.models import CustomUser
from .models import Ticket, TicketMessage


class SupportSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
        self.admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
        )
        self.admin.admin = True
        self.admin.save()

    def test_ticket_list_requires_login(self):
        """Testa que a listagem de tickets requer login"""
        response = self.client.get(reverse('support:ticket_list'))
        self.assertEqual(response.status_code, 302)

    def test_ticket_list_for_logged_user(self):
        """Testa listagem de tickets para usuário logado"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get(reverse('support:ticket_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_ticket(self):
        """Testa criação de ticket"""
        self.client.login(username='testuser', password='test123')
        response = self.client.post(reverse('support:ticket_create'), {
            'subject': 'Problema de teste',
            'message': 'Esta é uma mensagem de teste'
        })
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(TicketMessage.objects.count(), 1)

    def test_admin_sees_all_tickets(self):
        """Testa que admin vê todos os tickets"""
        # Cria ticket para usuário normal
        Ticket.objects.create(user=self.user, subject='Ticket do usuário')
        
        # Admin loga e acessa lista
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('support:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_admin_view'])
