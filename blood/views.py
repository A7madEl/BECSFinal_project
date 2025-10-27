from datetime import date
from io import BytesIO

from django.contrib import messages as dj_messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from reportlab.pdfgen import canvas

from .models import BLOOD_TYPES, Allocation, BloodRequest, BloodUnit, Donation
from .services import approve_and_allocate


# ---- simple role guard ----
def role_required(*roles):
    def deco(fn):
        def wrapper(request, *a, **kw):
            if not request.user.is_authenticated or request.user.role not in roles:
                return HttpResponseForbidden("Not allowed")
            return fn(request, *a, **kw)
        return wrapper
    return deco


# ---- dashboard ----
@login_required
def dashboard(request):
    return render(request, "blood/dashboard.html")


# ---- donor: donate ----
@role_required("DONOR")
def donate_new(request):
    if request.method == "POST":
        btype = request.POST["type"]
        collected_at = request.POST["collected_at"]
        volume_ml = int(request.POST.get("volume_ml", 450))
        site = request.POST.get("site", "")

        unit = BloodUnit.objects.create(
            type=btype,
            collected_at=collected_at,
            volume_ml=volume_ml,
            status="IN_STOCK",
            donor=request.user,
        )
        Donation.objects.create(donor=request.user, blood_unit=unit, site=site)
        dj_messages.success(request, "Donation added successfully!")
        return redirect("dashboard")

    return render(
        request,
        "blood/donate_new.html",
        {"blood_types": BLOOD_TYPES, "today": date.today()},
    )


# ---- donor/patient: create request ----
@role_required("DONOR", "PATIENT")
def request_new(request):
    if request.method == "POST":
        BloodRequest.objects.create(
            requester=request.user,
            requested_type=request.POST["requested_type"],
            quantity_units=int(request.POST["quantity_units"]),
            urgency=request.POST.get("urgency", "ROUTINE"),
        )
        dj_messages.success(request, "Blood request submitted.")
        return redirect("request_mine")
    return render(request, "blood/request_new.html", {"blood_types": BLOOD_TYPES})


# ---- donor/patient: my requests ----
@role_required("DONOR", "PATIENT")
def request_mine(request):
    items = BloodRequest.objects.filter(requester=request.user).order_by("-created_at")
    return render(request, "blood/request_mine.html", {"items": items})


# ---- doctor: manage requests ----
@role_required("DOCTOR")
def doctor_requests(request):
    items = BloodRequest.objects.select_related("requester").order_by("-created_at")
    return render(request, "blood/doctor_requests.html", {"items": items})


@role_required("DOCTOR")
def request_approve(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("POST required")

    req = get_object_or_404(BloodRequest, pk=pk)

    if req.status not in ("PENDING", "PARTIAL"):
        dj_messages.info(request, "Request is not pending/partial; nothing to approve.")
        return redirect("doctor_requests")

    allocations = approve_and_allocate(req, request.user)

    if allocations:
        if req.status == "FULFILLED":
            dj_messages.success(
                request, f"Approved and allocated {len(allocations)} unit(s). Request fulfilled."
            )
        else:
            dj_messages.warning(
                request, f"Approved and allocated {len(allocations)} unit(s). Still partial."
            )
    else:
        dj_messages.warning(
            request, "No compatible units available. Request remains pending."
        )

    return redirect("doctor_requests")


@role_required("DOCTOR")
def request_reject(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("POST required")

    req = get_object_or_404(BloodRequest, pk=pk)

    if req.status in ("FULFILLED",):
        dj_messages.info(request, "Request already fulfilled; cannot reject.")
        return redirect("doctor_requests")

    if req.status == "REJECTED":
        dj_messages.info(request, "Request already rejected.")
        return redirect("doctor_requests")

    req.status = "REJECTED"
    req.save(update_fields=["status"])
    dj_messages.info(request, "Request rejected.")
    return redirect("doctor_requests")


# ---- stock views (doctor & student) ----
@role_required("DOCTOR", "STUDENT")
def stock_view(request):
    rows = (
        BloodUnit.objects.filter(status="IN_STOCK")
        .values("type")
        .annotate(total=Count("id"))
        .order_by("type")
    )
    return render(request, "blood/stock_view.html", {"rows": rows})


# ---- PDF export (doctor & student) ----
def _render_stock_pdf(title, rows):
    buf = BytesIO()
    p = canvas.Canvas(buf)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, 800, title)
    y = 770
    for r in rows:
        p.setFont("Helvetica", 12)
        line = f"{r['type']}: {r['total']} units"
        p.drawString(40, y, line)
        y -= 18
        if y < 60:
            p.showPage()
            y = 800
    p.showPage()
    p.save()
    buf.seek(0)
    return buf.getvalue()


@role_required("DOCTOR", "STUDENT")
def stock_pdf(request):
    rows = (
        BloodUnit.objects.filter(status="IN_STOCK")
        .values("type")
        .annotate(total=Count("id"))
        .order_by("type")
    )
    pdf = _render_stock_pdf("Stock Report", rows)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'inline; filename="stock.pdf"'
    return resp


# student routes reuse stock_view & stock_pdf (already allowed by decorator)
student_stock = stock_view
student_stock_pdf = stock_pdf
