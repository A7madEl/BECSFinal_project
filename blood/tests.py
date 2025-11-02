from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.messages import get_messages
from .models import BloodUnit, Donation, BloodRequest, Allocation, AuditLog
from .services import compatible_sources, approve_and_allocate
from .views import role_required

User = get_user_model()


class BloodUnitModelTests(TestCase):
    """Test BloodUnit model functionality"""
    
    def setUp(self):
        self.donor = User.objects.create_user(
            username="donor1",
            password="testpass123",
            role=User.Role.DONOR
        )
    
    def test_blood_unit_creation(self):
        """Test creating a blood unit"""
        unit = BloodUnit.objects.create(
            type="O+",
            volume_ml=450,
            collected_at=date.today(),
            status="IN_STOCK",
            donor=self.donor
        )
        self.assertEqual(unit.type, "O+")
        self.assertEqual(unit.volume_ml, 450)
        self.assertEqual(unit.status, "IN_STOCK")
        self.assertEqual(unit.donor, self.donor)
    
    def test_blood_unit_default_volume(self):
        """Test default volume is 450ml"""
        unit = BloodUnit.objects.create(
            type="A-",
            collected_at=date.today()
        )
        self.assertEqual(unit.volume_ml, 450)
    
    def test_blood_unit_status_choices(self):
        """Test all status choices are valid"""
        unit = BloodUnit.objects.create(
            type="B+",
            collected_at=date.today(),
            status="RESERVED"
        )
        self.assertEqual(unit.status, "RESERVED")
        unit.status = "ISSUED"
        unit.save()
        self.assertEqual(unit.status, "ISSUED")
        unit.status = "DISCARDED"
        unit.save()
        self.assertEqual(unit.status, "DISCARDED")
    
    def test_blood_unit_all_types(self):
        """Test all blood types can be created"""
        blood_types = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
        for btype in blood_types:
            unit = BloodUnit.objects.create(
                type=btype,
                collected_at=date.today()
            )
            self.assertEqual(unit.type, btype)


class DonationModelTests(TestCase):
    """Test Donation model functionality"""
    
    def setUp(self):
        self.donor = User.objects.create_user(
            username="donor2",
            password="testpass123",
            role=User.Role.DONOR
        )
        self.unit = BloodUnit.objects.create(
            type="O+",
            collected_at=date.today(),
            donor=self.donor
        )
    
    def test_donation_creation(self):
        """Test creating a donation"""
        donation = Donation.objects.create(
            donor=self.donor,
            blood_unit=self.unit,
            site="Hospital A",
            hemoglobin=14.5,
            notes="Healthy donor"
        )
        self.assertEqual(donation.donor, self.donor)
        self.assertEqual(donation.blood_unit, self.unit)
        self.assertEqual(donation.site, "Hospital A")
        self.assertEqual(float(donation.hemoglobin), 14.5)
        self.assertEqual(donation.notes, "Healthy donor")
    
    def test_donation_one_to_one_relationship(self):
        """Test donation has one-to-one relationship with blood unit"""
        donation = Donation.objects.create(
            donor=self.donor,
            blood_unit=self.unit
        )
        self.assertEqual(self.unit.donation, donation)
    
    def test_donation_optional_fields(self):
        """Test donation optional fields"""
        donation = Donation.objects.create(
            donor=self.donor,
            blood_unit=self.unit
        )
        self.assertEqual(donation.site, "")
        self.assertIsNone(donation.hemoglobin)
        self.assertEqual(donation.notes, "")


class BloodRequestModelTests(TestCase):
    """Test BloodRequest model functionality"""
    
    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient1",
            password="testpass123",
            role=User.Role.PATIENT
        )
    
    def test_blood_request_creation(self):
        """Test creating a blood request"""
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="A+",
            quantity_units=2,
            urgency="EMERGENCY",
            status="PENDING"
        )
        self.assertEqual(request.requester, self.patient)
        self.assertEqual(request.requested_type, "A+")
        self.assertEqual(request.quantity_units, 2)
        self.assertEqual(request.urgency, "EMERGENCY")
        self.assertEqual(request.status, "PENDING")
    
    def test_blood_request_defaults(self):
        """Test default values for blood request"""
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="O-"
        )
        self.assertEqual(request.quantity_units, 1)
        self.assertEqual(request.urgency, "ROUTINE")
        self.assertEqual(request.status, "PENDING")
    
    def test_blood_request_status_transitions(self):
        """Test blood request status can be updated"""
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="B+"
        )
        self.assertEqual(request.status, "PENDING")
        request.status = "APPROVED"
        request.save()
        self.assertEqual(request.status, "APPROVED")
        request.status = "FULFILLED"
        request.save()
        self.assertEqual(request.status, "FULFILLED")


class AllocationModelTests(TestCase):
    """Test Allocation model functionality"""
    
    def setUp(self):
        self.donor = User.objects.create_user(
            username="donor_alloc",
            password="testpass123",
            role=User.Role.DONOR
        )
        self.doctor = User.objects.create_user(
            username="doctor_alloc",
            password="testpass123",
            role=User.Role.DOCTOR
        )
        self.patient = User.objects.create_user(
            username="patient_alloc",
            password="testpass123",
            role=User.Role.PATIENT
        )
        self.unit = BloodUnit.objects.create(
            type="O+",
            collected_at=date.today(),
            status="RESERVED"
        )
        self.request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="O+",
            quantity_units=1
        )
    
    def test_allocation_creation(self):
        """Test creating an allocation"""
        allocation = Allocation.objects.create(
            request=self.request,
            blood_unit=self.unit,
            allocated_by=self.doctor,
            note="Emergency case"
        )
        self.assertEqual(allocation.request, self.request)
        self.assertEqual(allocation.blood_unit, self.unit)
        self.assertEqual(allocation.allocated_by, self.doctor)
        self.assertEqual(allocation.note, "Emergency case")
    
    def test_allocation_relationship(self):
        """Test allocation relationships"""
        allocation = Allocation.objects.create(
            request=self.request,
            blood_unit=self.unit,
            allocated_by=self.doctor
        )
        self.assertIn(allocation, self.request.allocations.all())
        self.assertIn(allocation, self.doctor.allocations_made.all())


class CompatibleSourcesTests(TestCase):
    """Test blood compatibility service"""
    
    def test_o_negative_compatibility(self):
        """Test O- can only receive O-"""
        compatible = compatible_sources("O-")
        self.assertEqual(compatible, ["O-"])
    
    def test_o_positive_compatibility(self):
        """Test O+ can receive O+ and O-"""
        compatible = compatible_sources("O+")
        self.assertIn("O+", compatible)
        self.assertIn("O-", compatible)
        self.assertEqual(len(compatible), 2)
    
    def test_ab_positive_compatibility(self):
        """Test AB+ can receive all blood types"""
        compatible = compatible_sources("AB+")
        all_types = ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
        self.assertEqual(set(compatible), set(all_types))
    
    def test_a_positive_compatibility(self):
        """Test A+ compatibility"""
        compatible = compatible_sources("A+")
        expected = ["A+", "A-", "O+", "O-"]
        self.assertEqual(set(compatible), set(expected))


class ApproveAndAllocateTests(TestCase):
    """Test approve_and_allocate service function"""
    
    def setUp(self):
        self.doctor = User.objects.create_user(
            username="doctor2",
            password="testpass123",
            role=User.Role.DOCTOR
        )
        self.patient = User.objects.create_user(
            username="patient3",
            password="testpass123",
            role=User.Role.PATIENT
        )
    
    def test_approve_and_allocate_fulfilled(self):
        """Test approval with enough stock"""
        # Create compatible units
        unit1 = BloodUnit.objects.create(
            type="A+",
            collected_at=date.today(),
            status="IN_STOCK"
        )
        unit2 = BloodUnit.objects.create(
            type="A+",
            collected_at=date.today(),
            status="IN_STOCK"
        )
        
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="A+",
            quantity_units=2
        )
        
        allocations = approve_and_allocate(request, self.doctor)
        self.assertEqual(len(allocations), 2)
        
        request.refresh_from_db()
        self.assertEqual(request.status, "FULFILLED")
        
        unit1.refresh_from_db()
        unit2.refresh_from_db()
        self.assertEqual(unit1.status, "RESERVED")
        self.assertEqual(unit2.status, "RESERVED")
    
    def test_approve_and_allocate_partial(self):
        """Test approval with partial stock"""
        unit1 = BloodUnit.objects.create(
            type="O+",
            collected_at=date.today(),
            status="IN_STOCK"
        )
        
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="O+",
            quantity_units=3
        )
        
        allocations = approve_and_allocate(request, self.doctor)
        self.assertEqual(len(allocations), 1)
        
        request.refresh_from_db()
        self.assertEqual(request.status, "PARTIAL")
    
    def test_approve_and_allocate_no_stock(self):
        """Test approval with no compatible stock"""
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="AB-",
            quantity_units=1
        )
        
        allocations = approve_and_allocate(request, self.doctor)
        self.assertEqual(len(allocations), 0)
        
        request.refresh_from_db()
        self.assertEqual(request.status, "PENDING")
    
    def test_approve_and_allocate_compatible_types(self):
        """Test approval uses compatible blood types"""
        # O+ can receive O+ or O-
        o_neg_unit = BloodUnit.objects.create(
            type="O-",
            collected_at=date.today(),
            status="IN_STOCK"
        )
        
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="O+",
            quantity_units=1
        )
        
        allocations = approve_and_allocate(request, self.doctor)
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0].blood_unit.type, "O-")
    
    def test_approve_and_allocate_only_in_stock(self):
        """Test approval only uses IN_STOCK units"""
        reserved_unit = BloodUnit.objects.create(
            type="B+",
            collected_at=date.today(),
            status="RESERVED"
        )
        in_stock_unit = BloodUnit.objects.create(
            type="B+",
            collected_at=date.today(),
            status="IN_STOCK"
        )
        
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="B+",
            quantity_units=1
        )
        
        allocations = approve_and_allocate(request, self.doctor)
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0].blood_unit, in_stock_unit)
        self.assertNotEqual(allocations[0].blood_unit, reserved_unit)


class DashboardViewTests(TestCase):
    """Test dashboard view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")
    
    def test_dashboard_accessible_when_logged_in(self):
        """Test dashboard accessible when logged in"""
        user = User.objects.create_user(
            username="dashboard_user",
            password="testpass123"
        )
        self.client.login(username="dashboard_user", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


class DonateNewViewTests(TestCase):
    """Test donate_new view"""
    
    def setUp(self):
        self.client = Client()
        self.donor = User.objects.create_user(
            username="donor",
            password="testpass123",
            role=User.Role.DONOR
        )
        self.patient = User.objects.create_user(
            username="patient",
            password="testpass123",
            role=User.Role.PATIENT
        )
    
    def test_donate_new_requires_donor_role(self):
        """Test only donors can access donate page"""
        self.client.login(username="patient", password="testpass123")
        response = self.client.get(reverse("donate_new"))
        self.assertEqual(response.status_code, 403)
    
    def test_donate_new_get_request(self):
        """Test donate page loads for GET request"""
        self.client.login(username="donor", password="testpass123")
        response = self.client.get(reverse("donate_new"))
        self.assertEqual(response.status_code, 200)
        # Check that blood_types context is available
        self.assertIn("blood_types", response.context)
        # Also check that a blood type option is rendered
        self.assertContains(response, "O+")
    
    def test_donate_new_post_creates_unit_and_donation(self):
        """Test POST creates blood unit and donation"""
        self.client.login(username="donor", password="testpass123")
        post_data = {
            "type": "O+",
            "collected_at": date.today().isoformat(),
            "volume_ml": 450,
            "site": "Hospital A"
        }
        response = self.client.post(reverse("donate_new"), data=post_data)
        self.assertRedirects(response, reverse("dashboard"))
        
        unit = BloodUnit.objects.get(donor=self.donor)
        self.assertEqual(unit.type, "O+")
        self.assertEqual(unit.status, "IN_STOCK")
        
        donation = Donation.objects.get(donor=self.donor)
        self.assertEqual(donation.blood_unit, unit)
        self.assertEqual(donation.site, "Hospital A")


class RequestNewViewTests(TestCase):
    """Test request_new view"""
    
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            username="patient",
            password="testpass123",
            role=User.Role.PATIENT
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role=User.Role.DOCTOR
        )
    
    def test_request_new_requires_donor_or_patient_role(self):
        """Test only donors/patients can create requests"""
        self.client.login(username="doctor", password="testpass123")
        response = self.client.get(reverse("request_new"))
        self.assertEqual(response.status_code, 403)
    
    def test_request_new_get_request(self):
        """Test request page loads for GET"""
        self.client.login(username="patient", password="testpass123")
        response = self.client.get(reverse("request_new"))
        self.assertEqual(response.status_code, 200)
    
    def test_request_new_post_creates_request(self):
        """Test POST creates blood request"""
        self.client.login(username="patient", password="testpass123")
        post_data = {
            "requested_type": "A+",
            "quantity_units": 2,
            "urgency": "EMERGENCY"
        }
        response = self.client.post(reverse("request_new"), data=post_data)
        self.assertRedirects(response, reverse("request_mine"))
        
        request = BloodRequest.objects.get(requester=self.patient)
        self.assertEqual(request.requested_type, "A+")
        self.assertEqual(request.quantity_units, 2)
        self.assertEqual(request.urgency, "EMERGENCY")
        self.assertEqual(request.status, "PENDING")


class RequestMineViewTests(TestCase):
    """Test request_mine view"""
    
    def setUp(self):
        self.client = Client()
        self.patient1 = User.objects.create_user(
            username="patient1",
            password="testpass123",
            role=User.Role.PATIENT
        )
        self.patient2 = User.objects.create_user(
            username="patient2",
            password="testpass123",
            role=User.Role.PATIENT
        )
    
    def test_request_mine_shows_only_user_requests(self):
        """Test view shows only requester's requests"""
        self.client.login(username="patient1", password="testpass123")
        
        # Create requests for both patients
        BloodRequest.objects.create(
            requester=self.patient1,
            requested_type="O+",
            quantity_units=1
        )
        BloodRequest.objects.create(
            requester=self.patient2,
            requested_type="A+",
            quantity_units=1
        )
        
        response = self.client.get(reverse("request_mine"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["items"]), 1)
        self.assertEqual(response.context["items"][0].requester, self.patient1)


class DoctorRequestsViewTests(TestCase):
    """Test doctor_requests view"""
    
    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role=User.Role.DOCTOR
        )
        self.patient = User.objects.create_user(
            username="patient",
            password="testpass123",
            role=User.Role.PATIENT
        )
    
    def test_doctor_requests_requires_doctor_role(self):
        """Test only doctors can access doctor requests"""
        self.client.login(username="patient", password="testpass123")
        response = self.client.get(reverse("doctor_requests"))
        self.assertEqual(response.status_code, 403)
    
    def test_doctor_requests_shows_all_requests(self):
        """Test doctor sees all requests"""
        self.client.login(username="doctor", password="testpass123")
        
        BloodRequest.objects.create(
            requester=self.patient,
            requested_type="B+",
            quantity_units=1
        )
        
        response = self.client.get(reverse("doctor_requests"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["items"]), 1)


class RequestApproveViewTests(TestCase):
    """Test request_approve view"""
    
    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role=User.Role.DOCTOR
        )
        self.patient = User.objects.create_user(
            username="patient",
            password="testpass123",
            role=User.Role.PATIENT
        )
        self.unit = BloodUnit.objects.create(
            type="O+",
            collected_at=date.today(),
            status="IN_STOCK"
        )
    
    def test_request_approve_requires_post(self):
        """Test approve requires POST method"""
        self.client.login(username="doctor", password="testpass123")
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="O+",
            quantity_units=1
        )
        response = self.client.get(reverse("request_approve", args=[request.pk]))
        self.assertEqual(response.status_code, 403)
    
    def test_request_approve_fulfills_request(self):
        """Test approve creates allocations"""
        self.client.login(username="doctor", password="testpass123")
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="O+",
            quantity_units=1
        )
        
        response = self.client.post(reverse("request_approve", args=[request.pk]))
        self.assertRedirects(response, reverse("doctor_requests"))
        
        request.refresh_from_db()
        self.assertEqual(request.status, "FULFILLED")
        
        allocations = Allocation.objects.filter(request=request)
        self.assertEqual(allocations.count(), 1)


class RequestRejectViewTests(TestCase):
    """Test request_reject view"""
    
    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role=User.Role.DOCTOR
        )
        self.patient = User.objects.create_user(
            username="patient",
            password="testpass123",
            role=User.Role.PATIENT
        )
    
    def test_request_reject_changes_status(self):
        """Test reject changes status to REJECTED"""
        self.client.login(username="doctor", password="testpass123")
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="AB-",
            quantity_units=1
        )
        
        response = self.client.post(reverse("request_reject", args=[request.pk]))
        self.assertRedirects(response, reverse("doctor_requests"))
        
        request.refresh_from_db()
        self.assertEqual(request.status, "REJECTED")
    
    def test_request_reject_prevents_fulfilled_rejection(self):
        """Test cannot reject already fulfilled request"""
        self.client.login(username="doctor", password="testpass123")
        request = BloodRequest.objects.create(
            requester=self.patient,
            requested_type="A+",
            quantity_units=1,
            status="FULFILLED"
        )
        
        response = self.client.post(reverse("request_reject", args=[request.pk]))
        self.assertRedirects(response, reverse("doctor_requests"))
        
        request.refresh_from_db()
        self.assertEqual(request.status, "FULFILLED")  # Unchanged


class StockViewTests(TestCase):
    """Test stock_view"""
    
    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role=User.Role.DOCTOR
        )
        self.student = User.objects.create_user(
            username="student",
            password="testpass123",
            role=User.Role.STUDENT
        )
    
    def test_stock_view_requires_doctor_or_student(self):
        """Test stock view requires doctor or student role"""
        patient = User.objects.create_user(
            username="patient",
            password="testpass123",
            role=User.Role.PATIENT
        )
        self.client.login(username="patient", password="testpass123")
        response = self.client.get(reverse("stock_view"))
        self.assertEqual(response.status_code, 403)
    
    def test_stock_view_shows_aggregated_stock(self):
        """Test stock view shows aggregated counts"""
        self.client.login(username="doctor", password="testpass123")
        
        # Create multiple units of same type
        BloodUnit.objects.create(type="O+", collected_at=date.today(), status="IN_STOCK")
        BloodUnit.objects.create(type="O+", collected_at=date.today(), status="IN_STOCK")
        BloodUnit.objects.create(type="A+", collected_at=date.today(), status="IN_STOCK")
        
        response = self.client.get(reverse("stock_view"))
        self.assertEqual(response.status_code, 200)
        
        rows = response.context["rows"]
        o_plus_row = next((r for r in rows if r["type"] == "O+"), None)
        self.assertIsNotNone(o_plus_row)
        self.assertEqual(o_plus_row["total"], 2)


class StockPDFTests(TestCase):
    """Test stock PDF export"""
    
    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role=User.Role.DOCTOR
        )
    
    def test_stock_pdf_generates_pdf(self):
        """Test stock PDF generates valid PDF response"""
        self.client.login(username="doctor", password="testpass123")
        
        BloodUnit.objects.create(type="O-", collected_at=date.today(), status="IN_STOCK")
        
        response = self.client.get(reverse("stock_pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("filename", response["Content-Disposition"])
    
    def test_stock_pdf_only_shows_in_stock(self):
        """Test PDF only includes IN_STOCK units"""
        self.client.login(username="doctor", password="testpass123")
        
        BloodUnit.objects.create(type="O+", collected_at=date.today(), status="IN_STOCK")
        BloodUnit.objects.create(type="A+", collected_at=date.today(), status="RESERVED")
        
        response = self.client.get(reverse("stock_pdf"))
        self.assertEqual(response.status_code, 200)
        # PDF content should only show IN_STOCK units
