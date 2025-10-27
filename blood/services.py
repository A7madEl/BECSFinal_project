from datetime import date
from .models import BloodUnit, BloodRequest, Allocation
from django.db import transaction

COMPAT = {
    "O-": ["O-"],
    "O+": ["O+","O-"],
    "A-": ["A-","O-"],
    "A+": ["A+","A-","O+","O-"],
    "B-": ["B-","O-"],
    "B+": ["B+","B-","O+","O-"],
    "AB-": ["AB-","A-","B-","O-"],
    "AB+": ["AB+","AB-","A+","A-","B+","B-","O+","O-"],  # universal recipient
}

def compatible_sources(recipient_type: str):
    return COMPAT[recipient_type]

from django.db import transaction
from .models import BloodUnit, BloodRequest, Allocation

# compatibility map – keep yours if you already have it elsewhere
COMPAT = {
    "O-": ["O-"],
    "O+": ["O+", "O-"],
    "A-": ["A-", "O-"],
    "A+": ["A+", "A-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
}

def compatible_sources(recipient_type: str):
    return COMPAT[recipient_type]

@transaction.atomic
def approve_and_allocate(request: BloodRequest, doctor) -> list[Allocation]:
    """
    Approves a request and reserves compatible IN_STOCK units (oldest first).
    Returns created Allocation records. Sets status to FULFILLED or PARTIAL.
    """
    if request.status not in ("PENDING", "PARTIAL"):
        return []  # nothing to do

    needed = request.quantity_units
    plan: list[Allocation] = []

    # Get compatible units, oldest first. If you have collected_at True, prefer order_by("collected_at", "id")
    qs = (
        BloodUnit.objects
        .filter(status="IN_STOCK", type__in=compatible_sources(request.requested_type))
        .order_by("id")
    )

    for unit in qs:
        if needed == 0:
            break
        unit.status = "RESERVED"
        unit.save(update_fields=["status"])
        plan.append(Allocation.objects.create(request=request, blood_unit=unit, allocated_by=doctor))
        needed -= 1

    # set status
    if needed == 0:
        request.status = "FULFILLED"
    else:
        # if we allocated at least 1, mark PARTIAL; otherwise keep PENDING
        request.status = "PARTIAL" if plan else "PENDING"
    request.save(update_fields=["status"])

    return plan


def emergency_allocate_o_neg(quantity: int) -> list[BloodUnit]:
    qs = BloodUnit.objects.filter(status="IN_STOCK", type="O-", expires_at__gte=date.today()
          ).order_by("expires_at")[:quantity]
    units = list(qs)
    for u in units:
        u.status = "RESERVED"
        u.save(update_fields=["status"])
    return units
