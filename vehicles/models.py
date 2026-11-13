from django.db import models


class Vehicle(models.Model):
    FUEL_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('CNG', 'CNG'),
        ('ELECTRIC', 'Electric'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('IN_SERVICE', 'In service'),
        ('INACTIVE', 'Inactive'),
    ]

    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES)
    current_odometer = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='ACTIVE')

    insurance_provider = models.CharField(max_length=100)
    insurance_policy_number = models.CharField(max_length=50)
    insurance_expiry = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_number} ({self.make} {self.model})"

    
class VehicleAssignment(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.driver} -> {self.vehicle.registration_number}"
    
class MileageLog(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='mileage_logs',
    )
    driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='mileage_logs',
    )
    date = models.DateField()
    odometer_reading = models.PositiveIntegerField()
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date', '-odometer_reading']

    def __str__(self):
        return f"{self.vehicle.registration_number}: {self.odometer_reading} km on {self.date}"