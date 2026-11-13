from django.conf import settings
from django.db import models


class DriverProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'DRIVER'},
    )
    phone = models.CharField(max_length=15)
    license_number = models.CharField(max_length=30, unique=True)
    license_expiry = models.DateField()

    def __str__(self):
        return self.user.get_full_name() or self.user.username