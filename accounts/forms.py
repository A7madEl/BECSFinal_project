from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignupForm(UserCreationForm):
    ROLE_CHOICES = [
        ("DONOR", "Donor"),
        ("PATIENT", "Patient"),
    ]
    # extra (optional) fields you already have on the model
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    national_id = forms.CharField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "national_id", "role", "password1", "password2")
