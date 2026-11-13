from datetime import timedelta

from django.conf import settings
from django.db import models


class MaintenanceSchedule(models.Model):
    SERVICE_CHOICES = [
        ('OIL', 'Oil change'),
        ('TYRE', 'Tyre rotation'),
        ('BRAKE', 'Brake check'),
        ('GENERAL', 'General service'),
        ('OTHER', 'Other'),
    ]

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='schedules',
    )
    service_type = models.CharField(max_length=10, choices=SERVICE_CHOICES)
    interval_km = models.PositiveIntegerField(null=True, blank=True)
    interval_days = models.PositiveIntegerField(null=True, blank=True)
    last_service_km = models.PositiveIntegerField(default=0)
    last_service_date = models.DateField(null=True, blank=True)

    @property
    def next_due_km(self):
        if self.interval_km:
            return self.last_service_km + self.interval_km
        return None

    @property
    def next_due_date(self):
        if self.interval_days and self.last_service_date:
            return self.last_service_date + timedelta(days=self.interval_days)
        return None

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.vehicle.registration_number}"


class MaintenanceRecord(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending approval'),
        ('APPROVED', 'Approved'),
    ]

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='maintenance_records',
    )
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='records',
    )
    service_date = models.DateField()
    odometer = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    workshop = models.CharField(max_length=100)
    notes = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.vehicle.registration_number} service on {self.service_date}"

class IssueReport(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('RESOLVED', 'Resolved'),
    ]

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='issues',
    )
    driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues',
    )
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle.registration_number}: {self.description[:40]}"    