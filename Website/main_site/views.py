from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate
from .forms import CustomUserCreationForm
from .models import UserProfile, Stacks, Deployments, DeploymentFrontend, DeploymentBackend, DeploymentDatabase
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests

DEPLOY_BOX_API_URL = 'http://34.68.6.54:5000/api'

# Basic Routes
def home(request):
    return render(request, "home.html", {})

def stacks(request):
    return render(request, "stacks.html", {})

def pricing(request):
    return render(request, "pricing.html", {})

def maintenance(request):
    return render(request, "maintenance.html", {})

# Authentication
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_token(request):
    # Token is automatically validated via Django OAuth2 backend
    return JsonResponse({"message": "Token is valid!"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    """Return information about the authenticated user."""
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_stacks(request):
    user = request.user
    stacks = user.stacks_set.all()
    return Response(stacks.values(), status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_deployments(request):
    user = request.user
    deployments = user.deployments_set.all()
    return Response(deployments.values(), status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_stack(request):
    user = request.user
    stack_type = request.data.get('type')
    variant = request.data.get('variant')
    version = request.data.get('version')

    if not type or not variant or not version:
        return Response({'error': 'Type, variant, and version are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the stack already exists
    if Stacks.objects.filter(user=user, type=stack_type, variant=variant, version=version).exists():
        return Response({'error': 'Stack already exists'}, status=status.HTTP_400_BAD_REQUEST)

    Stacks.objects.create(user=user, type=stack_type, variant=variant, version=version)
    return Response({'message': 'Stack added successfully'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_deployment(request):
    user = request.user
    deployment_name = request.data.get('name')
    deployment_stack_id = request.data.get('stack_id')
    tar_file = request.FILES.get('file')

    if not deployment_name:
        return Response({'error': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not deployment_stack_id:
        return Response({'error': 'Stack ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not tar_file:
        return Response({'error': 'File is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Find the stack for the deployment
    try:
        stack = Stacks.objects.get(id=deployment_stack_id, user=user)
    except Stacks.DoesNotExist:
        return Response({'error': 'Stack not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create the deployment record in the database
    deployment = Deployments.objects.create(user=user, name=deployment_name, stack=stack)

    json_data = {
        'stack-type': stack.type,
        'deployment-id': deployment.id
    }

    # Stream the file to the destination API
    try:
        response = requests.post(f'{DEPLOY_BOX_API_URL}/code', files=request.FILES, data=json_data, stream=True)
        if response.status_code != 200:
            return Response(response.json(), status=response.status_code)

        # Create the frontend, backend, and database records in the database
        deployment_data = response.json()
        DeploymentFrontend.objects.create(deployment=deployment, url=deployment_data['frontend_id'], image_url=deployment_data['frontend_image'])
        DeploymentBackend.objects.create(deployment=deployment, url=deployment_data['backend_id'], image_url=deployment_data['backend_image'])
        DeploymentDatabase.objects.create(deployment=deployment, uri=deployment_data['database_uri'], project_id=deployment_data['project_id'])

        return Response({'message': 'Deployment added successfully'}, status=status.HTTP_201_CREATED)

    except requests.RequestException as e:
        return Response({'error': f'Error communicating with destination API: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def patch_deployment(request):
    user = request.user
    deployment_id = request.data.get('deployment-id')
    tar_file = request.FILES.get('file')

    if not deployment_id:
        return Response({'error': 'Deployment ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not tar_file:
        return Response({'error': 'File is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Find the deployment
    try:
        deployment = Deployments.objects.get(id=deployment_id, user=user)
    except Deployments.DoesNotExist:
        return Response({'error': 'Deployment not found.'}, status=status.HTTP_404_NOT_FOUND)

    deploymentfrontend = DeploymentFrontend.objects.get(deployment=deployment)
    deploymentbackend = DeploymentBackend.objects.get(deployment=deployment)
    deploymentdatabase = DeploymentDatabase.objects.get(deployment=deployment)

    json_data = {
        'deployment-id': deployment_id,
        'stack-type': deployment.stack.type,
        'frontend-url': deploymentfrontend.url,
        'frontend-image': deploymentfrontend.image_url,
        'backend-url': deploymentbackend.url,
        'backend-image': deploymentbackend.image_url,
        'database-uri': deploymentdatabase.uri,
        'project-id': deploymentdatabase.project_id
    }

    # Stream the file to the destination API
    try:
        response = requests.patch(f'{DEPLOY_BOX_API_URL}/api/code', files=request.FILES, data=json_data, stream=True)
        if response.status_code != 200:
            return Response(response.json(), status=response.status_code)

        return Response({'message': 'Deployment updated successfully'}, status=status.HTTP_201_CREATED)

    except requests.RequestException as e:
        return Response({'error': f'Error communicating with destination API: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_stack(request, stack_id):
    user = request.user

    stack = Stacks.objects.get(id=stack_id, user=user)

    source_code = requests.get(f'{DEPLOY_BOX_API_URL}/code/{stack.type}')
    if source_code.status_code != 200:
        return Response({'error': 'Failed to download stack'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response = HttpResponse(source_code.content, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{stack.type}.zip"'
    return response
    