from django.core.management.base import BaseCommand

from alerts.models import Alert
from alerts.services import generate_alerts


class Command(BaseCommand):
    help = 'Create and refresh maintenance, insurance and licence alerts'

    def handle(self, *args, **options):
        generate_alerts()
        self.stdout.write(self.style.SUCCESS(f'Alerts updated. Active alerts: {Alert.objects.count()}'))