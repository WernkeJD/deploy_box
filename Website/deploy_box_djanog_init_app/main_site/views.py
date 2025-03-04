from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.forms import UserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout, authenticate
from .forms import CustomUserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User


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

@api_view(['POST'])
def verify_user_credentials(request):
    """
    Verifies user credentials (username and password) from the CLI.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is not None:
        return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
#container views
@api_view(['GET'])
def get_container_access(request):
    username = request.data.get ('username')

    auth_user = User.objects.get(username=username)
    user_id = auth_user.id
    user = UserProfile.objects.get(user_id=user_id)

    # Fetch the user's profile
    profile = UserProfile.objects.get(user=user)

    # Return the list of containers the user has access to
    access_data = {
        'has_mern': profile.has_mern
    }

    return JsonResponse(access_data, status=200)