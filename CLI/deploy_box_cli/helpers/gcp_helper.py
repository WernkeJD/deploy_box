from google.cloud import storage

import os
import time
from google.oauth2 import service_account
import docker
import google.auth
import google.auth.transport.requests
from .decorators import singleton


@singleton
class GCPHelper:
    def __init__(self, cli_dir: str):
        from deploy_box_cli.helpers import AuthHelper, DockerHelper

        self.auth = AuthHelper()
        self.docker = DockerHelper()
        self.project_id = "deploy-box"
        self.gcloud_key_path = None
        self.deployment_id = None

    def get_gcloud_cli_key(self, deployment_id: str):
        # Get the Google key
        response = self.auth.request_api(
            "GET",
            f"deployments/{deployment_id}/key",
        )
        if not response.ok:
            print(f"Error: {response.status_code}")
            print(f"Error: {response.json()['error']}")
            return

        google_key = response.json()["data"]

        self.gcloud_key_path = os.path.join(f"google_key_{deployment_id}.json")
        self.deployment_id = deployment_id

        # TODO: Find a secure way to save the Google key
        # Save the Google key to a file
        with open(self.gcloud_key_path, "w") as file:
            file.write(google_key)

    def upload_to_bucket(self, file_path: str):
        if not self.gcloud_key_path:
            print("Google key path is not set.")
            return

        bucket_name = f"deploy-box-bucket-{self.deployment_id}"

        # Initialize the Google Cloud Storage client
        client = storage.Client.from_service_account_json(self.gcloud_key_path)

        try:
            # Get the bucket
            bucket = client.bucket(bucket_name)

            # Upload the file
            blob = bucket.blob("file.tar")
            blob.upload_from_filename(file_path)

            # Remove the local file after upload
            os.remove(file_path)

        except Exception as e:
            print(f"Error uploading to GCP bucket: {e}")
            raise

        print("Upload completed successfully.")

    def configure_docker_auth(self):
        """Configure Docker to authenticate with Google Cloud Artifact Registry."""
        if not self.gcloud_key_path:
            print("Google key path is not set.")
            return

        credentials = service_account.Credentials.from_service_account_file(
            self.gcloud_key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # Get the access token
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        token = credentials.token

        # Configure Docker client
        client = docker.from_env()

        # Authenticate Docker with the Artifact Registry
        auth_config = {
            "username": "oauth2accesstoken",
            "password": token,
            "registry": "us-central1-docker.pkg.dev",
        }

        client.login(**auth_config)
        print("Docker authenticated with us-central1-docker.pkg.dev")

    def build_and_push_images(self):
        """Build and push frontend and backend Docker images to GCP Artifact Registry."""
        if not self.gcloud_key_path:
            print("Google key path is not set.")
            return

        # Configure Docker authentication
        self.configure_docker_auth()

        # Build and push the frontend image
        frontend_image_name = f"us-central1-docker.pkg.dev/deploy-box/deploy-box-repo-{self.deployment_id}/frontend:{int(time.time())}"
        frontend_source_directory = os.path.join(os.getcwd(), "frontend")
        self.docker.build_image(frontend_image_name, frontend_source_directory)
        self.docker.push_image(frontend_image_name)

        # Build and push the backend image
        backend_image_name = f"us-central1-docker.pkg.dev/deploy-box/deploy-box-repo-{self.deployment_id}/backend:{int(time.time())}"
        backend_source_directory = os.path.join(os.getcwd(), "backend")
        self.docker.build_image(backend_image_name, backend_source_directory)
        self.docker.push_image(backend_image_name)

        return frontend_image_name, backend_image_name
