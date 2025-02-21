from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import CustomUserCreationForm
from .models import UserProfile

#Basic Route Return Functions

def home(request):
    return render(request, "home.html", {})

def stacks(request):
    return render(request, "stacks.html", {})

def pricing(request):
    return render(request, "pricing.html", {})

def maintenance(request):
    return render(request, "maintenance.html", {})

#authentication endpoints

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            name = form.cleaned_data['name']
            birthdate = form.cleaned_data['birthdate']
            
            # Create UserProfile after user creation
            UserProfile.objects.create(user=user, name=name, birthdate=birthdate)
            
            return redirect('/accounts/login')  # Redirect to login page after signup
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})