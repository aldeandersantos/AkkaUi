import pytest
from support.models import Ticket, TicketMessage
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.models
@pytest.mark.django_db
class TestTicketModel:
    def test_create_ticket(self, user):
        ticket = Ticket.objects.create(
            user=user,
            subject='Test Subject'
        )
        assert ticket.user == user
        assert ticket.subject == 'Test Subject'
        assert ticket.status == 'open'
    
    def test_ticket_status_choices(self, user):
        for status in ['open', 'in_progress', 'closed']:
            ticket = Ticket.objects.create(
                user=user,
                subject=f'Ticket {status}',
                status=status
            )
            assert ticket.status == status
    
    def test_ticket_default_status(self, user):
        ticket = Ticket.objects.create(
            user=user,
            subject='Default Status Test'
        )
        assert ticket.status == 'open'
    
    def test_ticket_allow_client_uploads_default(self, user):
        ticket = Ticket.objects.create(
            user=user,
            subject='Upload Test'
        )
        assert ticket.allow_client_uploads is False
    
    def test_ticket_str_representation(self, user):
        ticket = Ticket.objects.create(
            user=user,
            subject='Test Ticket'
        )
        str_repr = str(ticket)
        assert 'Test Ticket' in str_repr
        assert user.username in str_repr
    
    def test_ticket_timestamps(self, user):
        ticket = Ticket.objects.create(
            user=user,
            subject='Timestamp Test'
        )
        assert ticket.created_at is not None
        assert ticket.updated_at is not None
    
    def test_ticket_ordering(self, user):
        ticket1 = Ticket.objects.create(user=user, subject='First')
        ticket2 = Ticket.objects.create(user=user, subject='Second')
        
        tickets = Ticket.objects.all()
        assert tickets[0] == ticket2
        assert tickets[1] == ticket1


@pytest.mark.models
@pytest.mark.django_db
class TestTicketMessageModel:
    def test_create_ticket_message(self, user):
        ticket = Ticket.objects.create(
            user=user,
            subject='Test'
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=user,
            message='Test message content'
        )
        assert message.ticket == ticket
        assert message.user == user
        assert message.message == 'Test message content'
    
    def test_ticket_message_default_is_staff_reply(self, user):
        ticket = Ticket.objects.create(user=user, subject='Test')
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=user,
            message='Message'
        )
        assert message.is_staff_reply is False
    
    def test_ticket_message_staff_reply(self, admin_user):
        ticket = Ticket.objects.create(
            user=admin_user,
            subject='Test'
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=admin_user,
            message='Staff reply',
            is_staff_reply=True
        )
        assert message.is_staff_reply is True
    
    def test_ticket_message_str_representation(self, user):
        ticket = Ticket.objects.create(user=user, subject='Test')
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=user,
            message='Test'
        )
        str_repr = str(message)
        assert user.username in str_repr
    
    def test_ticket_message_ordering(self, user):
        ticket = Ticket.objects.create(user=user, subject='Test')
        msg1 = TicketMessage.objects.create(
            ticket=ticket,
            user=user,
            message='First'
        )
        msg2 = TicketMessage.objects.create(
            ticket=ticket,
            user=user,
            message='Second'
        )
        
        messages = TicketMessage.objects.all()
        assert messages[0] == msg1
        assert messages[1] == msg2
    
    def test_ticket_message_with_attachment(self, user):
        ticket = Ticket.objects.create(user=user, subject='Test')
        
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=user,
            message='Message with attachment'
        )
        # Default attachment should be falsy (None or empty)
        assert not message.attachment
