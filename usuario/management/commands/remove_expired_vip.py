from django.core.management.base import BaseCommand
from django.utils import timezone
from usuario.models import CustomUser

class Command(BaseCommand):
    help = 'Desativa VIP de usuários cuja data de expiração já passou.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired_vips = CustomUser.objects.filter(is_vip=True, vip_expiration__lt=today)
        count = expired_vips.count()
        for user in expired_vips:
            user.is_vip = False
            user.save(update_fields=["is_vip"])
            self.stdout.write(self.style.WARNING(f"VIP removido de: {user.username}"))
        self.stdout.write(self.style.SUCCESS(f"{count} usuários tiveram o VIP removido."))
