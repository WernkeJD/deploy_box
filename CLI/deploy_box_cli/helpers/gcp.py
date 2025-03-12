import subprocess
import os
from deploy_box_cli.helpers.auth import AuthHelper
from deploy_box_cli.helpers.docker import DockerHelper
import time


class GCPHelper:
    def __init__(self, auth: AuthHelper, cli_dir: str):
        self.auth = auth
        self.gcloud_cli_path = os.path.join(
            cli_dir, "helpers", "google-cloud-sdk", "bin", "gcloud"
        )

        self.project_id = "deploy-box"
        self.gcloud_cli_key_path = None
        self.deployment_id = None

    def get_gcloud_cli_key(self, deployment_id: str):
        # Get the Google CLI key
        response = self.auth.request_api(
            "GET",
            f"deployments/{deployment_id}/key",
        )
        if not response.ok:
            print(f"Error: {response.status_code}")
            print(f"Error: {response.json()['error']}")
            return

        google_cli_key = response.json()["data"]

        # TODO: Find a secure way to save the Google CLI key
        # Save the Google CLI key to a file

        self.gcloud_cli_key_path = os.path.join(f"google_cli_key_{deployment_id}.json")
        self.deployment_id = deployment_id

        # TODO: Find a secure way to save the Google CLI key
        # Save the Google CLI key to a file
        with open(self.gcloud_cli_key_path, "w") as file:
            file.write(google_cli_key)

        self.__auth_gcloud()

    def __auth_gcloud(self):
        if not self.gcloud_cli_key_path:
            print("Google CLI key path is not set.")
            return

        # Initialize the gcloud CLI
        try:
            subprocess.run(
                [
                    self.gcloud_cli_path,
                    "auth",
                    "activate-service-account",
                    f"--key-file={self.gcloud_cli_key_path}",
                ],
                check=True,
            )
            subprocess.run(
                [
                    self.gcloud_cli_path,
                    "auth",
                    "configure-docker",
                    "us-central1-docker.pkg.dev",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error initializing gcloud CLI: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")

    def upload_to_bucket(self, file_path: str):
        if not self.gcloud_cli_key_path:
            print("Google CLI key path is not set.")
            return

        bucket_name = f"deploy-box-bucket-{self.deployment_id}"
        # Upload the source code to the GCP bucket
        try:
            subprocess.run(
                [
                    self.gcloud_cli_path,
                    "storage",
                    "cp",
                    file_path,
                    f"gs://{bucket_name}/file.tar",
                ],
                check=True,
            )

            # Remove the local file after upload
            os.remove(file_path)

        except subprocess.CalledProcessError as e:
            print(f"Error uploading to GCP bucket: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
        print("Upload completed successfully.")

    def upload_to_artifact_registry(self) -> tuple[str, str]:
        if not self.gcloud_cli_key_path:
            print("Google CLI key path is not set.")
            return

        # Upload the docker image to the GCP artifact registry
        try:
            # Build the frontend image
            frontend_image_name = f"us-central1-docker.pkg.dev/deploy-box/deploy-box-repo-{self.deployment_id}/frontend:{int(time.time())}"
            source_directory = os.path.join(os.getcwd(), "frontend")
            DockerHelper.build_image(
                frontend_image_name,
                source_directory,
            )

            # Push the frontend image to the GCP artifact registry
            DockerHelper.push_image(frontend_image_name)

            # Build the backend image
            backend_image_name = f"us-central1-docker.pkg.dev/deploy-box/deploy-box-repo-{self.deployment_id}/backend:{int(time.time())}"
            source_directory = os.path.join(os.getcwd(), "backend")
            DockerHelper.build_image(
                backend_image_name,
                source_directory,
            )

            # Push the backend image to the GCP artifact registry
            DockerHelper.push_image(backend_image_name)

            return frontend_image_name, backend_image_name

        except subprocess.CalledProcessError as e:
            print(f"Error uploading to GCP artifact registry: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
        print("Upload completed successfully.")
