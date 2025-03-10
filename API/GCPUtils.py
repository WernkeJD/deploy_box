from google.cloud import run_v2
from google.iam.v1 import policy_pb2
from google.auth import load_credentials_from_file
from google.protobuf.duration_pb2 import Duration
from google.cloud import storage

PROJECT_ID = "deploy-box"
REGION = "us-central1"
BUCKET_NAME = "deploy_box_bucket"

credentials, project_id = load_credentials_from_file("key.json")

run_client = run_v2.ServicesClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

def get_blob(blob_name):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    return blob

def deploy_service(service_name, image, env_vars):
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
    # Update service to use new image
    parent = f"projects/{PROJECT_ID}/locations/{REGION}"
    service_full_name = f"{parent}/services/{service_name}"

    service = run_client.get_service(name=service_full_name)

    service.template.containers[0].image = image

    operation = run_client.update_service(service=service)
    operation.result()  # Wait for deployment
    print(f"Refreshed {service_name}")

