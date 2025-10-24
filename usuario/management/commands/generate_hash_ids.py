from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
import secrets
import hashlib
import time


class Command(BaseCommand):
    help = "Gera hash_id para usuários existentes sem hash_id"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Não salva alterações, apenas mostra quantos seriam atualizados",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Número de objetos processados por commit (padrão: 100)",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        qs = User.objects.filter(Q(hash_id__isnull=True) | Q(hash_id=""))
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhum usuário sem hash_id encontrado."))
            return

        if options.get("dry_run"):
            self.stdout.write(f"DRY RUN: {total} usuários seriam atualizados.")
            return

        updated = 0
        batch_size = max(1, options.get("batch_size") or 100)

        # Processa em lotes para evitar usar muita memória e permitir commits
        with transaction.atomic():
            iterator = qs.iterator()
            batch = []
            for user in iterator:
                if not user.hash_id:
                    try:
                        user.hash_id = secrets.token_hex(32)
                    except Exception:
                        # Fallback seguro
                        user.hash_id = hashlib.sha256(
                            f"{user.username}-{time.time()}".encode()
                        ).hexdigest()
                    batch.append(user)

                if len(batch) >= batch_size:
                    for u in batch:
                        u.save(update_fields=["hash_id"])
                    updated += len(batch)
                    batch = []

            # salva o que restou
            if batch:
                for u in batch:
                    u.save(update_fields=["hash_id"])
                updated += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Atualizados {updated}/{total} usuários."))