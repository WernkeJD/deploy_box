from ..models import Stacks
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from ..serializers.stacks_serializer import StacksSerializer
import requests
from django.http import FileResponse
from google.cloud import storage
import os
from google.oauth2 import service_account
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


def get_stacks(request: Request, stack_id: str = None) -> Response:
    user = request.user

    if stack_id:
        try:
            stack = Stacks.objects.get(id=stack_id, user=user)
            stack = StacksSerializer(stack).data
            return Response({"data": stack}, status=status.HTTP_200_OK)
        except Stacks.DoesNotExist:

            return Response({"error": "Stack Not Found"}, status.HTTP_404_NOT_FOUND)
    else:
        stacks = Stacks.objects.filter(user=user)
        stacks = StacksSerializer(stacks, many=True).data
        return Response({"data": stacks}, status.HTTP_200_OK)


def add_stack(request: Request) -> Response:
    user = request.user
    stack_type = request.data.get("type")
    variant = request.data.get("variant")
    version = request.data.get("version")

    if not stack_type or not variant or not version:
        return Response(
            {"error": "Type, variant, and version are required."},
            status.HTTP_400_BAD_REQUEST,
        )

    if Stacks.objects.filter(
        user=user, type=stack_type, variant=variant, version=version
    ).exists():
        return Response({"error": "Stack already exists"}, status.HTTP_400_BAD_REQUEST)

    Stacks.objects.create(user=user, type=stack_type, variant=variant, version=version)
    return Response({"message": "Stack added successfully"}, status.HTTP_201_CREATED)


def update_stack(request: Request, stack_id: str) -> Response:
    if not stack_id:
        return Response(
            {"error": "Stack ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    stack = get_stacks(request, stack_id)
    if not stack:
        return Response({"error": "Stack not found."}, status=status.HTTP_404_NOT_FOUND)

    stack_type = request.data.get("type", stack.type)
    variant = request.data.get("variant", stack.variant)
    version = request.data.get("version", stack.version)

    stack.type = stack_type
    stack.variant = variant
    stack.version = version
    stack.save()

    return Response({"message": "Stack updated successfully"}, status.HTTP_200_OK)

def download_stack(request: Request, stack_id: str = None) -> Response:
    if not stack_id:
        return Response({"error": "Stack ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the user's stack or return 404
    stack = get_object_or_404(Stacks, id=stack_id, user=request.user)

    # Load service account credentials
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'key.json')
    
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = storage.Client(credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    bucket_name = "deploy_box_bucket"
    blob_name = f"{stack.stack.type.upper()}.tar"

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Ensure the file exists before attempting to download
        if not blob.exists(client):
            return Response({"error": "File not found in bucket"}, status=status.HTTP_404_NOT_FOUND)

        # Stream the file response instead of loading everything into memory
        response = FileResponse(blob.open("rb"), content_type="application/x-tar")
        response["Content-Disposition"] = f'attachment; filename="{blob_name}"'
        return response

    except Exception as e:
        logger.error(f"Error downloading stack {stack_id}: {e}")
        return Response({"error": "Error downloading stack."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # user = request.user

    # print(stack_id)
    # if not stack_id:
    #     return Response({"error": "Stack ID is required."}, status.HTTP_400_BAD_REQUEST)

    # try:
    #     stack = Stacks.objects.get(id=stack_id, user=user)
    # except Stacks.DoesNotExist:
    #     return Response({"error": "Stack not found."}, status.HTTP_404_NOT_FOUND)

    # try:
    #     source_code = requests.get(
    #         f"{DEPLOY_BOX_API_URL}/code/{stack.type}", stream=True
    #     )

    #     if source_code.status_code != 200:
    #         return Response(
    #             {"error": "Error downloading stack"},
    #             status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         )

    #     # Use FileResponse to stream the tar file as a binary response
    #     response = FileResponse(
    #         source_code.raw, content_type="application/x-tar", status=status.HTTP_200_OK
    #     )
    #     response["Content-Disposition"] = f'attachment; filename="{stack.type}.tar"'
    #     return response

    # except requests.RequestException as e:
    #     return Response(
    #         {"error": f"Error downloading stack: {str(e)}"},
    #         status.HTTP_500_INTERNAL_SERVER_ERROR,
    #     )
