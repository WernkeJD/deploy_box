from ..models import (
    Deployments,
    DeploymentFrontend,
    DeploymentBackend,
    DeploymentDatabase,
    Stacks,
)
import requests
from rest_framework import status
from pymongo import MongoClient
from rest_framework.request import Request
from rest_framework.response import Response
from api.serializers import DeploymentsSerializer
from api.utils import gcp_utils, mongodb_utils


# Function to get all deployments or a specific deployment
def get_deployments(request: Request, deployment_id=None) -> Response:
    user = request.user

    if deployment_id:
        deployment = Deployments.objects.filter(id=deployment_id, user=user).first()
        if not deployment:
            return Response({"error": "Deployment not found."}, status.HTTP_404_NOT_FOUND)

        return Response({"data": deployment}, status.HTTP_200_OK)

    deployments = Deployments.objects.filter(user=user)
    deployments = DeploymentsSerializer(deployments, many=True).data
    return Response({"data": deployments}, status.HTTP_200_OK)


# Function to upload a new deployment
def add_deployment(request: Request) -> Response:
    user = request.user

    stack_id = request.data.get("stack_id")
    name= request.data.get("name")

    if not all([stack_id, name]):
        return Response({"error": "Stack ID and name are required."}, status.HTTP_400_BAD_REQUEST)
    
    stack = Stacks.objects.filter(id=stack_id, user=user).first()
    if not stack:
        return Response({"error": "Stack not found."}, status.HTTP_404_NOT_FOUND)
        
    deployment = Deployments.objects.create(
        stack=stack,
        user=user,
        name=name,
    )

    deployment_id = str(deployment.id)

    try:

        google_cli_key = gcp_utils.create_service_account(deployment_id)
        deployment.google_cli_key = google_cli_key

        deployment.save()

        # Create deployment database
        mongo_db_uri = mongodb_utils.deploy_mongodb_database(deployment_id)
        deployment_database = DeploymentDatabase.objects.create(
            deployment=deployment,
            uri=mongo_db_uri,
        )

        # Create deployment backend
        # TODO: Use the backend image from the stack
        backend_image = "kalebwbishop/mern-backend"
        backend_url = gcp_utils.deploy_service(
            f"backend-{deployment_id}", backend_image, {"MONGO_URI": mongo_db_uri}
        )
    
        deployment_backend = DeploymentBackend.objects.create(
            deployment=deployment,
            url=backend_url,
            image_url=backend_image,
        )

        # Create deployment frontend
        # TODO: Use the frontend image from the stack
        frontend_image = "kalebwbishop/mern-frontend"
        frontend_url = gcp_utils.deploy_service(
            f"frontend-{deployment_id}",
            frontend_image,
            {"REACT_APP_BACKEND_URL": backend_url},
        )

        deployment_frontend = DeploymentFrontend.objects.create(
            deployment=deployment,
            url=frontend_url,
            image_url=frontend_image,
        )

        # Save the deployment details
        deployment_database.save()
        deployment_backend.save()
        deployment_frontend.save()
        deployment.save()

    except Exception as e:
        deployment.delete()

        return Response(
            {"error": "Failed to create service account."},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    


    return Response(
        {
            "data": DeploymentsSerializer(deployment).data,
        },
        status.HTTP_201_CREATED,
    )


# Get deployment google cli key
def get_deployment_google_cli_key(request: Request, deployment_id: str) -> Response:
    user = request.user
    deployment = Deployments.objects.filter(id=deployment_id, user=user).first()
    if not deployment:
        return Response({"error": "Deployment not found."}, status.HTTP_404_NOT_FOUND)

    google_cli_key = deployment.google_cli_key
    if not google_cli_key:
        return Response({"error": "Google CLI key not found."}, status.HTTP_404_NOT_FOUND)

    return Response({"data": google_cli_key}, status.HTTP_200_OK)

def patch_deployment(request: Request, deployment_id: str) -> Response:
    user = request.user
    deployment = Deployments.objects.filter(id=deployment_id, user=user).first()
    if not deployment:
        return Response({"error": "Deployment not found."}, status.HTTP_404_NOT_FOUND)
    
    deployment_backend = request.data.get("backend")
    deployment_frontend = request.data.get("frontend")
    
    if not all([deployment_backend, deployment_frontend]):
        return Response({"error": "Backend and frontend image urls are required."}, status.HTTP_400_BAD_REQUEST)
    
    gcp_utils.refresh_service(
        f"backend-{deployment_id}",
        deployment_backend.image_url,
    )
    gcp_utils.refresh_service(
        f"frontend-{deployment_id}",
        deployment_frontend.image_url,
    )
    return Response({"message": "Deployment updated successfully."}, status.HTTP_200_OK)


def get_deployment_cost(request, deployment_id):
    user = request.user
    # deployment = Deployments.objects.filter(id=deployment_id, user=user).first()
    # if not deployment:
    #     return Response({"error": "Deployment not found."}, status.HTTP_404_NOT_FOUND)

    # deployment_backend = DeploymentBackend.objects.filter(deployment=deployment).first()

    # if not deployment_backend:
    #     return Response({"error": "Deployment backend not found."}, status.HTTP_404_NOT_FOUND)

    # client = MongoClient(deployment_backend.uri)
    client = MongoClient(
        "mongodb+srv://deployBoxAdmin:Dramatic23@cluster0.yjaoi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )

    db_id = "1"

    db = client[f"db-{db_id}"]

    stats = db.command("dbstats")

    return Response({"data": stats}, status.HTTP_200_OK)
