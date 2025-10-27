from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL

BLOOD_TYPES = [
    ("O-", "O-"), ("O+", "O+"), ("A-", "A-"), ("A+", "A+"),
    ("B-", "B-"), ("B+", "B+"), ("AB-", "AB-"), ("AB+", "AB+"),
]

class BloodUnit(models.Model):
    type = models.CharField(max_length=4, choices=BLOOD_TYPES)
    volume_ml = models.PositiveIntegerField(default=450)
    collected_at = models.DateField()
    status = models.CharField(max_length=16, choices=[
        ("IN_STOCK","IN_STOCK"), ("RESERVED","RESERVED"),
        ("ISSUED","ISSUED"), ("DISCARDED","DISCARDED")
    ], default="IN_STOCK")
    donor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="donated_units")

class Donation(models.Model):
    donor = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={"role":"DONOR"})
    blood_unit = models.OneToOneField(BloodUnit, on_delete=models.PROTECT, related_name="donation")
    site = models.CharField(max_length=64, blank=True)
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class BloodRequest(models.Model):
    URGENCY = [("ROUTINE","ROUTINE"),("EMERGENCY","EMERGENCY")]
    STATUS = [("PENDING","PENDING"),("APPROVED","APPROVED"),("REJECTED","REJECTED"),
              ("FULFILLED","FULFILLED"),("PARTIAL","PARTIAL")]
    requester = models.ForeignKey(User, on_delete=models.PROTECT)  # donor/patient
    requested_type = models.CharField(max_length=4, choices=BLOOD_TYPES)
    quantity_units = models.PositiveIntegerField(default=1)
    urgency = models.CharField(max_length=16, choices=URGENCY, default="ROUTINE")
    status = models.CharField(max_length=16, choices=STATUS, default="PENDING")
    doctor_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Allocation(models.Model):
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name="allocations")
    blood_unit = models.ForeignKey(BloodUnit, on_delete=models.PROTECT)
    allocated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="allocations_made")
    allocated_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=128, blank=True)

class AuditLog(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    target = models.CharField(max_length=64)   # e.g., "BloodRequest#15"
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    ts = models.DateTimeField(auto_now_add=True)
