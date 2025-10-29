from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from .forms import SignupForm
from .models import User

def home(request):
    return render(request, "home.html")

def signup(request):
    if request.user.is_authenticated:
        # already logged in — send to dashboard
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            # enforce only DONOR/PATIENT at signup
            role = form.cleaned_data["role"]
            if role not in ("DONOR", "PATIENT"):
                dj_messages.error(request, "Invalid role.")
                return render(request, "registration/signup.html", {"form": form})

            user: User = form.save(commit=False)
            user.role = role
            user.is_active = True
            user.save()

            dj_messages.success(request, "Account created! You can log in now.")
            return redirect("login")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})
