from django.db import models


class FuelLog(models.Model):
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='fuel_logs',
    )
    driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_logs',
    )
    date = models.DateField()
    litres = models.DecimalField(max_digits=7, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    odometer = models.PositiveIntegerField()

    class Meta:
        ordering = ['-date']

    @property
    def price_per_litre(self):
        if self.litres:
            return round(self.total_cost / self.litres, 2)
        return 0

    def __str__(self):
        return f"Fuel {self.vehicle.registration_number} on {self.date}"


class RepairExpense(models.Model):
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='repair_expenses',
    )
    date = models.DateField()
    description = models.CharField(max_length=200)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    workshop = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Repair {self.vehicle.registration_number}: {self.description}"