from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=100)
    birthdate = forms.DateField()

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'name', 'birthdate']

