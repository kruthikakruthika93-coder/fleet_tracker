from django.db import models
from django.utils import timezone


class Alert(models.Model):
    TYPE_CHOICES = [
        ('INSURANCE', 'Insurance expiry'),
        ('SERVICE_KM', 'Service due by distance'),
        ('SERVICE_DATE', 'Service due by date'),
        ('LICENSE', 'Driver licence expiry'),
    ]

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
    )
    driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
    )
    alert_type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    message = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_read', '-created_at']

    @property
    def days_left(self):
        if self.due_date:
            return (self.due_date - timezone.localdate()).days
        return None

    @property
    def level(self):
        if self.days_left is not None and self.days_left < 0:
            return 'danger'
        return 'warning'

    def __str__(self):
        return self.message