from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Document

class Command(BaseCommand):
    help = 'Delete all expired documents'

    def handle(self, *args, **kwargs):
        expired = Document.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()
        for doc in expired:
            doc.file.delete()
            doc.delete()
        self.stdout.write(f'Deleted {count} expired document(s).')