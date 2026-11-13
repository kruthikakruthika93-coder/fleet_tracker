from datetime import timedelta

from django.db import models
from django.utils import timezone

ACTIVE_WINDOW = timedelta(minutes=2)


class DriverLocation(models.Model):
    driver = models.OneToOneField(
        'drivers.DriverProfile',
        on_delete=models.CASCADE,
        related_name='location',
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)
    is_sharing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    @property
    def status(self):
        if not self.is_sharing:
            return 'OFFLINE'
        if timezone.now() - self.updated_at <= ACTIVE_WINDOW:
            return 'ACTIVE'
        return 'OUTDATED'

    def __str__(self):
        return f"{self.driver}: {self.latitude}, {self.longitude}"