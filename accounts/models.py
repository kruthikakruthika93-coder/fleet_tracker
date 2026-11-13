from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DRIVER', 'Driver'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='DRIVER')

    def __str__(self):
        return f"{self.username} ({self.role})"