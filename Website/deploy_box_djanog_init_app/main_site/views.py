from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.forms import UserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout, authenticate
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

@api_view(['POST'])
def verify_user_credentials(request):
    """
    Verifies user credentials (username and password).
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is not None:
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({'message': 'Login successful', 'access_token': access_token}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    
#containers endpoints
@api_view(['PATCH'])
def update_container_access(request):
    username = request.data.get('username')
    has_mern = request.data.get('has_mern')

    try:
        user = UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get or create the user's profile (if it doesn't exist yet)
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Update the user's access to containers
    profile.has_mern = has_mern


    profile.save()

    return Response({'message': 'User container access updated successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_container_access(request):
    # Optionally, authenticate the user
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    # Get the user's profile
    user = request.user  # Using the logged-in user from the request
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

    # Retrieve container access information
    access_data = {
        'has_mern': profile.has_mern
    }

    return Response(access_data, status=status.HTTP_200_OK)