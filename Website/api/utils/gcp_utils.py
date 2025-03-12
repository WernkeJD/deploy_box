import subprocess
import os
from google.cloud import run_v2
from google.iam.v1 import policy_pb2
from google.auth import load_credentials_from_file
from google.protobuf.duration_pb2 import Duration
from google.cloud import storage

current_working_dir = os.getcwd()
gcloud_cli_path = os.path.join(
    current_working_dir, "api", "utils", "google-cloud-sdk", "bin", "gcloud"
)
gcloud_cli_key_path = os.path.join(
    current_working_dir, "api", "key.json"
)

PROJECT_ID = "deploy-box"
REGION = "us-central1"
BUCKET_NAME = "deploy_box_bucket"

def init_gcloud():
    # Initialize the gcloud CLI
    try:
        subprocess.run([gcloud_cli_path, "auth", "activate-service-account", f"--key-file={gcloud_cli_key_path}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error initializing gcloud CLI: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")


def create_service_account(deployment_id: str):
    init_gcloud()
    service_account_name = f"deploy-box-sa-{deployment_id}"
    project_id = "deploy-box"

    # TODO: Use the sdk instead of the cli

    try:
        # Check if the service account already exists
        output = subprocess.run(
            [
                gcloud_cli_path,
                "iam",
                "service-accounts",
                "list",
                "--project",
                project_id,
            ],
            check=True,
            capture_output=True,
        )

        service_accounts = output.stdout.decode("utf-8").splitlines()
        for account in service_accounts:
            if service_account_name in account:
                print(f"Service account {service_account_name} already exists.")
                return
                

        # Create a service account
        subprocess.run(
            [
                gcloud_cli_path,
                "iam",
                "service-accounts",
                "create",
                service_account_name,
                "--description=Service account for deploy box",
                "--display-name=Deploy Box Service Account",
                f"--project={project_id}",
            ],
            check=True,
        )

        # Create a repository
        repository_name = f"deploy-box-repo-{deployment_id}"

        subprocess.run(
            [
                gcloud_cli_path,
                "artifacts",
                "repositories",
                "create",
                repository_name,
                "--repository-format=docker",
                "--location=us-central1",
                f"--project={project_id}",
            ],
            check=True,
        )

        # Add IAM policy binding
        subprocess.run(
            [
                "gcloud",
                "artifacts",
                "repositories",
                "add-iam-policy-binding",
                repository_name,
                "--location=us-central1",
                f"--member=serviceAccount:{service_account_name}@{project_id}.iam.gserviceaccount.com",
                "--role=projects/deploy-box/roles/deployBoxArtifactRegistryReadWriteRole",
            ],
            check=True,
        )

        # Create a storage bucket
        bucket_name = f"gs://deploy-box-bucket-{deployment_id}"
        subprocess.run(
            [
                gcloud_cli_path,
                "storage",
                "buckets",
                "create",
                bucket_name,
                "--location=us-central1",
                f"--project={project_id}",
            ],
            check=True,
        )
        # Add IAM policy binding for the bucket
        subprocess.run(
            [
                gcloud_cli_path,
                "storage",
                "buckets",
                "add-iam-policy-binding",
                bucket_name,
                f"--member=serviceAccount:{service_account_name}@{project_id}.iam.gserviceaccount.com",
                "--role=projects/deploy-box/roles/deployBoxArtifactRegistryReadWriteRole",
                f"--project={project_id}",
            ],
            check=True,
        )

        # Create a key for the service account
        service_account_key_path = os.path.join(
            current_working_dir, "api", "utils", f"{service_account_name}-key.json"
        )
        key = subprocess.run(
            [
            gcloud_cli_path,
            "iam",
            "service-accounts",
            "keys",
            "create",
            service_account_key_path,
            f"--iam-account={service_account_name}@{project_id}.iam.gserviceaccount.com",
            f"--project={project_id}",
            ],
            check=True,
        )

        with open(service_account_key_path, "r") as file:
            key_data = file.read()

        # Clean up the key file
        os.remove(service_account_key_path)

        return key_data
    
    except subprocess.CalledProcessError as e:
        print(f"Error creating service account or key: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")

def deploy_service(service_name, image, env_vars):
    credentials, project_id = load_credentials_from_file(gcloud_cli_key_path)
    run_client = run_v2.ServicesClient(credentials=credentials)

    parent = f"projects/{PROJECT_ID}/locations/{REGION}"
    service_full_name = f"{parent}/services/{service_name}"

    print(f"env_vars {env_vars}")


    service = run_v2.Service(
        template=run_v2.RevisionTemplate(
            containers=[run_v2.Container(
                image=image,
                env=[run_v2.EnvVar(name=key, value=value) for key, value in env_vars.items()],
                ports=[run_v2.ContainerPort(container_port=8080)]
            )],
            timeout=Duration(seconds=300)  # 5 min timeout
        )
    )

    operation = run_client.create_service(
        parent=parent, 
        service=service, 
        service_id=service_name
    )

    operation.result()  # Wait for deployment
    print(f"Deployed {service_name}")

    # Add IAM policy binding
    policy = run_client.get_iam_policy(request={"resource": service_full_name})
    policy.bindings.append(
        policy_pb2.Binding(
            role="roles/run.invoker",
            members=["allUsers"]
        )
    )
    run_client.set_iam_policy(request={"resource": service_full_name, "policy": policy})
    # Get service URL
    service_info = run_client.get_service(name=service_full_name)
    return service_info.uri

def refresh_service(service_name, image):
    credentials, project_id = load_credentials_from_file(gcloud_cli_key_path)
    run_client = run_v2.ServicesClient(credentials=credentials)

    # Update service to use new image
    parent = f"projects/{PROJECT_ID}/locations/{REGION}"
    service_full_name = f"{parent}/services/{service_name}"

    service = run_client.get_service(name=service_full_name)

    service.template.containers[0].image = image

    operation = run_client.update_service(service=service)
    operation.result()  # Wait for deployment
    print(f"Refreshed {service_name}")