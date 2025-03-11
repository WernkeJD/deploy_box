from .models import (
    Stacks,
    Deployments,
    DeploymentFrontend,
    DeploymentBackend,
    DeploymentDatabase,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from .services import stack_services, deployment_services
import requests

DEPLOY_BOX_API_URL = "http://34.68.6.54:5000/api"
# DEPLOY_BOX_API_URL = "http://localhost:5000/api"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def testing(request: Request):
    return Response({"message": "Testing"}, status=status.HTTP_200_OK)


@api_view(["GET", "POST", "PATCH"])
@permission_classes([IsAuthenticated])
def stack_operations(request: Request, stack_id=None):
    # GET: Fetch available stacks or a specific stack
    if request.method == "GET":
        return stack_services.get_stacks(request, stack_id)

    # POST: Add a new stack
    elif request.method == "POST":
        return stack_services.add_stack(request)

    # PATCH: Update a stack
    elif request.method == "PATCH":
        return stack_services.update_stack(request, stack_id)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_available_deployments(request):
    user = request.user
    deployments = user.deployments_set.all()
    return Response(deployments.values(), status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_deployment(request):
    user = request.user
    deployment_name = request.data.get("name")
    deployment_stack_id = request.data.get("stack_id")
    tar_file = request.FILES.get("file")

    if not deployment_name:
        return Response(
            {"error": "Name is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not deployment_stack_id:
        return Response(
            {"error": "Stack ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not tar_file:
        return Response(
            {"error": "File is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Find the stack for the deployment
    try:
        stack = Stacks.objects.get(id=deployment_stack_id, user=user)
    except Stacks.DoesNotExist:
        return Response({"error": "Stack not found."}, status=status.HTTP_404_NOT_FOUND)

    # Create the deployment record in the database
    deployment = Deployments.objects.create(
        user=user, name=deployment_name, stack=stack
    )

    json_data = {"stack-type": stack.type, "deployment-id": deployment.id}

    # Stream the file to the destination API
    try:
        response = requests.post(
            f"{DEPLOY_BOX_API_URL}/code",
            files=request.FILES,
            data=json_data,
            stream=True,
        )
        if response.status_code != 200:
            return Response(response.json(), status=response.status_code)

        # Create the frontend, backend, and database records in the database
        deployment_data = response.json()
        DeploymentFrontend.objects.create(
            deployment=deployment,
            url=deployment_data["frontend_id"],
            image_url=deployment_data["frontend_image"],
        )
        DeploymentBackend.objects.create(
            deployment=deployment,
            url=deployment_data["backend_id"],
            image_url=deployment_data["backend_image"],
        )
        DeploymentDatabase.objects.create(
            deployment=deployment,
            uri=deployment_data["database_uri"],
            project_id=deployment_data["project_id"],
        )

        return Response(
            {"message": "Deployment added successfully"}, status=status.HTTP_201_CREATED
        )

    except requests.RequestException as e:
        return Response(
            {"error": f"Error communicating with destination API: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def patch_deployment(request):
    user = request.user
    deployment_id = request.data.get("deployment-id")
    tar_file = request.FILES.get("file")

    if not deployment_id:
        return Response(
            {"error": "Deployment ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not tar_file:
        return Response(
            {"error": "File is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Find the deployment
    try:
        deployment = Deployments.objects.get(id=deployment_id, user=user)
    except Deployments.DoesNotExist:
        return Response(
            {"error": "Deployment not found."}, status=status.HTTP_404_NOT_FOUND
        )

    deploymentfrontend = DeploymentFrontend.objects.get(deployment=deployment)
    deploymentbackend = DeploymentBackend.objects.get(deployment=deployment)
    deploymentdatabase = DeploymentDatabase.objects.get(deployment=deployment)

    json_data = {
        "deployment-id": deployment_id,
        "stack-type": deployment.stack.type,
        "frontend-url": deploymentfrontend.url,
        "frontend-image": deploymentfrontend.image_url,
        "backend-url": deploymentbackend.url,
        "backend-image": deploymentbackend.image_url,
        "database-uri": deploymentdatabase.uri,
        "project-id": deploymentdatabase.project_id,
    }

    # Stream the file to the destination API
    try:
        response = requests.patch(
            f"{DEPLOY_BOX_API_URL}/api/code",
            files=request.FILES,
            data=json_data,
            stream=True,
        )
        if response.status_code != 200:
            return Response(response.json(), status=response.status_code)

        return Response(
            {"message": "Deployment updated successfully"},
            status=status.HTTP_201_CREATED,
        )

    except requests.RequestException as e:
        return Response(
            {"error": f"Error communicating with destination API: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_deployment_details(request: Request, deployment_id: str):
    return deployment_services.get_deployment_cost(request, deployment_id)