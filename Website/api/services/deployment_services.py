from ..models import (
    Deployments,
    DeploymentFrontend,
    DeploymentBackend,
    DeploymentDatabase,
    Stacks,
)
import requests
from rest_framework import status
from rest_framework.response import Response
from pymongo import MongoClient


# Function to upload a new deployment
def upload_deployment(user, deployment_name, deployment_stack_id, tar_file):
    if not deployment_name or not deployment_stack_id or not tar_file:
        return {
            "error": "Name, Stack ID, and File are required."
        }, status.HTTP_400_BAD_REQUEST

    try:
        stack = Stacks.objects.get(id=deployment_stack_id, user=user)
    except Stacks.DoesNotExist:
        return {"error": "Stack not found."}, status.HTTP_404_NOT_FOUND

    # Create the deployment record in the database
    deployment = Deployments.objects.create(
        user=user, name=deployment_name, stack=stack
    )

    json_data = {"stack-type": stack.type, "deployment-id": deployment.id}

    # Stream the file to the destination API
    try:
        response = requests.post(
            f"http://localhost:5000/api/code",
            files={"file": tar_file},
            data=json_data,
            stream=True,
        )
        if response.status_code != 200:
            return response.json(), response.status_code

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

        return {"message": "Deployment added successfully"}, status.HTTP_201_CREATED

    except requests.RequestException as e:
        return {
            "error": f"Error communicating with destination API: {str(e)}"
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


# Function to update an existing deployment
def update_deployment(user, deployment_id, tar_file):
    if not deployment_id or not tar_file:
        return {
            "error": "Deployment ID and File are required."
        }, status.HTTP_400_BAD_REQUEST

    try:
        deployment = Deployments.objects.get(id=deployment_id, user=user)
    except Deployments.DoesNotExist:
        return {"error": "Deployment not found."}, status.HTTP_404_NOT_FOUND

    # Retrieve related deployment info
    frontend = DeploymentFrontend.objects.get(deployment=deployment)
    backend = DeploymentBackend.objects.get(deployment=deployment)
    database = DeploymentDatabase.objects.get(deployment=deployment)

    json_data = {
        "deployment-id": deployment_id,
        "stack-type": deployment.stack.type,
        "frontend-url": frontend.url,
        "frontend-image": frontend.image_url,
        "backend-url": backend.url,
        "backend-image": backend.image_url,
        "database-uri": database.uri,
        "project-id": database.project_id,
    }

    # Stream the file to the destination API for updating
    try:
        response = requests.patch(
            f"http://localhost:5000/api/code",
            files={"file": tar_file},
            data=json_data,
            stream=True,
        )
        if response.status_code != 200:
            return response.json(), response.status_code

        return {"message": "Deployment updated successfully"}, status.HTTP_200_OK

    except requests.RequestException as e:
        return {
            "error": f"Error communicating with destination API: {str(e)}"
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


# Function to handle stack download
def download_stack(user, stack_id):
    try:
        stack = Stacks.objects.get(id=stack_id, user=user)
    except Stacks.DoesNotExist:
        return {"error": "Stack not found."}, status.HTTP_404_NOT_FOUND

    try:
        source_code = requests.get(f"http://localhost:5000/api/code/{stack.type}")
        if source_code.status_code != 200:
            return {
                "error": "Failed to download stack"
            }, status.HTTP_500_INTERNAL_SERVER_ERROR

        return source_code.content, None  # Return the source code if successful

    except requests.RequestException as e:
        return {
            "error": f"Error downloading stack: {str(e)}"
        }, status.HTTP_500_INTERNAL_SERVER_ERROR

def delete_deployment(user, deployment_id):
    # TODO: Implement the delete deployment logic
    pass

def get_deployment_cost(request, deployment_id):
    user = request.user
    # deployment = Deployments.objects.filter(id=deployment_id, user=user).first()
    # if not deployment:
    #     return Response({"error": "Deployment not found."}, status.HTTP_404_NOT_FOUND)
    
    # deployment_backend = DeploymentBackend.objects.filter(deployment=deployment).first()

    # if not deployment_backend:
    #     return Response({"error": "Deployment backend not found."}, status.HTTP_404_NOT_FOUND)
    
    # client = MongoClient(deployment_backend.uri)
    client = MongoClient("mongodb+srv://deployBoxAdmin:Dramatic23@cluster0.yjaoi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

    db_id = '1'

    db = client[f'db-{db_id}']

    stats = db.command('dbstats')

    return Response({"data": stats}, status.HTTP_200_OK)