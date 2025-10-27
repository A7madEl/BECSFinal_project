from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        DONOR = "DONOR", "Donor"
        PATIENT = "PATIENT", "Patient"
        DOCTOR = "DOCTOR", "Doctor (Admin)"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.PATIENT)
    national_id = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=32, blank=True)
