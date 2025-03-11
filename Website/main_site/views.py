from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests


# Basic Routes
def home(request):
    return render(request, "home.html", {})


def stacks(request):
    return render(request, "stacks.html", {})


def pricing(request):
    return render(request, "pricing.html", {})

def profile(request):
    return render(request, "profile.html", {})

def maintenance(request):
    return render(request, "maintenance.html", {})
