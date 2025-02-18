from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

# Create your views here.

def home(request):
    return render(request, "home.html", {})