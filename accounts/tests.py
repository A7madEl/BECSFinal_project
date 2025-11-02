from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import User
from .forms import SignupForm

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test creating a user with all fields"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=User.Role.DONOR,
            national_id="123456789",
            phone="1234567890"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, User.Role.DONOR)
        self.assertEqual(user.national_id, "123456789")
        self.assertEqual(user.phone, "1234567890")
    
    def test_user_role_choices(self):
        """Test all role choices are available"""
        roles = [choice[0] for choice in User.Role.choices]
        self.assertIn("DONOR", roles)
        self.assertIn("PATIENT", roles)
        self.assertIn("DOCTOR", roles)
        self.assertIn("STUDENT", roles)
    
    def test_user_default_role(self):
        """Test default role is PATIENT"""
        user = User.objects.create_user(
            username="defaultuser",
            password="testpass123"
        )
        self.assertEqual(user.role, User.Role.PATIENT)
    
    def test_user_optional_fields(self):
        """Test that national_id and phone can be blank"""
        user = User.objects.create_user(
            username="optionaluser",
            password="testpass123"
        )
        self.assertEqual(user.national_id, "")
        self.assertEqual(user.phone, "")


class SignupFormTests(TestCase):
    """Test SignupForm validation"""
    
    def test_form_valid_with_donor_role(self):
        """Test form is valid with DONOR role"""
        form_data = {
            "username": "donor1",
            "email": "donor@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "DONOR",
            "phone": "1234567890",
            "national_id": "123456789"
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_valid_with_patient_role(self):
        """Test form is valid with PATIENT role"""
        form_data = {
            "username": "patient1",
            "email": "patient@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "PATIENT"
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_password_mismatch(self):
        """Test form validation fails with mismatched passwords"""
        form_data = {
            "username": "user1",
            "email": "user@example.com",
            "password1": "testpass123",
            "password2": "differentpass",
            "role": "DONOR"
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_form_optional_fields(self):
        """Test that email, phone, and national_id are optional"""
        form_data = {
            "username": "user2",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "PATIENT"
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())


class SignupViewTests(TestCase):
    """Test signup view functionality"""
    
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("signup")
    
    def test_signup_get_request(self):
        """Test signup page loads for GET request"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
    
    def test_signup_redirects_if_authenticated(self):
        """Test authenticated users are redirected from signup"""
        user = User.objects.create_user(
            username="loggedin",
            password="testpass123"
        )
        self.client.login(username="loggedin", password="testpass123")
        response = self.client.get(self.signup_url)
        self.assertRedirects(response, reverse("dashboard"))
    
    def test_signup_post_valid_donor(self):
        """Test successful signup with DONOR role"""
        form_data = {
            "username": "newdonor",
            "email": "donor@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "DONOR"
        }
        response = self.client.post(self.signup_url, data=form_data)
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newdonor").exists())
        user = User.objects.get(username="newdonor")
        self.assertEqual(user.role, User.Role.DONOR)
        self.assertTrue(user.is_active)
    
    def test_signup_post_valid_patient(self):
        """Test successful signup with PATIENT role"""
        form_data = {
            "username": "newpatient",
            "email": "patient@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "PATIENT"
        }
        response = self.client.post(self.signup_url, data=form_data)
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newpatient")
        self.assertEqual(user.role, User.Role.PATIENT)
    
    def test_signup_rejects_invalid_role(self):
        """Test signup rejects invalid roles (DOCTOR/STUDENT)"""
        # First test: Form validation rejects invalid role choice
        form_data = {
            "username": "hacker",
            "email": "hacker@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "DOCTOR"
        }
        response = self.client.post(self.signup_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        # Form should be invalid because DOCTOR is not in form choices
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="hacker").exists())
    
    def test_signup_invalid_form_data(self):
        """Test signup handles invalid form data"""
        form_data = {
            "username": "baduser",
            "password1": "short",
            "password2": "different",
            "role": "DONOR"
        }
        response = self.client.post(self.signup_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="baduser").exists())


class HomeViewTests(TestCase):
    """Test home view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_view_accessible(self):
        """Test home page is accessible without authentication"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
