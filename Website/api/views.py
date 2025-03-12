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
from .utils import gcp_utils

DEPLOY_BOX_API_URL = "http://34.68.6.54:5000/api"
# DEPLOY_BOX_API_URL = "http://localhost:5000/api"


@api_view(["GET"])
def testing(request: Request):
    # gcp_utils.create_service_account('6')

    return Response({"message": "Testing"}, status=status.HTTP_200_OK)


@api_view(["GET", "POST", "PATCH"])
def stack_operations(request: Request, stack_id=None):
    # GET: Fetch available stacks or a specific stack
    if request.method == "GET":
        if request.path.endswith("/download"):
            return stack_services.download_stack(request, stack_id)
        else:
            return stack_services.get_stacks(request, stack_id)

    # POST: Add a new stack
    elif request.method == "POST":
        return stack_services.add_stack(request)

    # PATCH: Update a stack
    elif request.method == "PATCH":
        return stack_services.update_stack(request, stack_id)
    
@api_view(["GET", "POST", "PATCH"])
def deployment_operations(request: Request, deployment_id=None):
    # GET: Fetch available deployments or a specific deployment
    if request.method == "GET":
        # TODO: Add logic to download deployment code
        if request.path.endswith("/key"):
            return deployment_services.get_deployment_google_cli_key(request, deployment_id)
        else:
            return deployment_services.get_deployments(request, deployment_id)

    # POST: Upload a new deployment
    elif request.method == "POST":
        return deployment_services.add_deployment(request)

    # PATCH: Update a deployment
    # elif request.method == "PATCH":
    #     return deployment_services.patch_deployment(request)


@api_view(["GET"])
def get_available_deployments(request):
    user = request.user
    deployments = user.deployments_set.all()
    return Response(deployments.values(), status=status.HTTP_200_OK)

@api_view(["GET"])
def get_deployment_details(request: Request, deployment_id: str):
    return deployment_services.get_deployment_cost(request, deployment_id)
