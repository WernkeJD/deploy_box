import os
import subprocess
from flask import Flask
from google.cloud import run_v2
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import docker
import time
import database
from cryptography.fernet import Fernet


# Set paths and credentials
current_working_dir = os.getcwd()
GCP_KEY_PATH = "./key.json"
PROJECT_ID = "deploy-box"
REGION = "us-central1"
name = f"projects/{PROJECT_ID}"
parent = f"{name}/locations/{REGION}"

app = Flask(__name__)
connection = database.get_connection()


# Helper function to load credentials
def get_credentials(scopes=None):
    return service_account.Credentials.from_service_account_file(
        GCP_KEY_PATH, scopes=scopes
    )


# Helper function to initialize services client
def get_services_client():
    return run_v2.ServicesClient(credentials=get_credentials())


def authenticate_docker():
    """Authenticate Docker using service account credentials."""
    credentials = get_credentials(
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    # Get the access token
    auth_req = Request()
    credentials.refresh(auth_req)
    token = credentials.token

    # Authenticate Docker with the Artifact Registry
    auth_config = {
        "username": "oauth2accesstoken",
        "password": token,
        "registry": "us-central1-docker.pkg.dev",
    }

    docker.from_env().login(**auth_config)

    print("Authenticated Docker with Google Container Registry")


def build_and_push_image(image_name, repo_path, tag: str = "latest"):
    """Builds and pushes a Docker image to Google Container Registry."""
    dockerfile_path = os.path.join(repo_path, "Dockerfile")

    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Error: Path {repo_path} does not exist.")
    if not os.path.exists(dockerfile_path):
        raise FileNotFoundError(f"Error: Dockerfile missing in {repo_path}.")

    image_tag = f"us-central1-docker.pkg.dev/{PROJECT_ID}/deploy-box-repository/{image_name}:{tag}"

    print(f"Building image: {image_tag}")

    authenticate_docker()

    try:
        subprocess.run(["docker", "build", "-t", image_tag, repo_path], check=True)
        print("Docker build completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")
        return

    try:
        subprocess.run(["docker", "push", image_tag], check=True)
        print("Docker push completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing Docker image: {e}")
        return

    return image_tag


# Function to refresh the service by updating the image
def refresh_service(service_name, image, tag="latest"):
    run_client = get_services_client()
    parent = f"projects/{PROJECT_ID}/locations/{REGION}"

    service_full_name = f"{parent}/services/{service_name}"
    service = run_client.get_service(name=service_full_name)

    service.template.containers[0].image = f"{image}:{tag}"
    operation = run_client.update_service(service=service)
    operation.result()  # Wait for deployment
    print(f"Refreshed {service_name}")


def clone_repo(repo_url, repo_name, access_token):
    """Clones the given GitHub repository to the server."""
    repo_path = os.path.abspath(
        os.path.join(
            current_working_dir,
            "deployed_repos",
            f"{repo_name}_{int(time.time())}",
        )
    ).replace("\\", "/")

    os.makedirs("deployed_repos", exist_ok=True)

    # Convert repo URL to use token authentication
    repo_url_with_auth = repo_url.replace(
        "https://github.com", f"https://{access_token}:x-oauth-basic@github.com"
    )

    try:
        subprocess.run(["git", "clone", repo_url_with_auth, repo_path], check=True)
        return repo_path
    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository: {e}")
        raise Exception(f"Failed to clone repository: {e}")


def clone_user_repo(repo_path, stack_id):

    tag = str(int(time.time()))

    build_and_push_image(f"frontend-{stack_id}", f"{repo_path}/frontend", tag=tag)
    build_and_push_image(f"backend-{stack_id}", f"{repo_path}/backend", tag=tag)

    refresh_service(
        f"frontend-{stack_id}",
        f"us-central1-docker.pkg.dev/{PROJECT_ID}/deploy-box-repository/frontend-{stack_id}",
        tag=tag,
    )
    refresh_service(
        f"backend-{stack_id}",
        f"us-central1-docker.pkg.dev/{PROJECT_ID}/deploy-box-repository/backend-{stack_id}",
        tag=tag,
    )

    return repo_path


ENCRYPTION_KEY = os.getenv("GITHUB_TOKEN_KEY")


def get_github_access_token(user_id: str):
    cursor = connection.cursor()

    cursor.execute(
        "SELECT encrypted_token FROM github_tokens WHERE user_id = %s", (user_id,)
    )
    rows = cursor.fetchone()
    cipher = Fernet(ENCRYPTION_KEY)
    decrypted_token = cipher.decrypt(rows[0].tobytes())
    decoded_token = decrypted_token.decode()
    return decoded_token


@app.route("/github-webhook", methods=["GET"])
def get_github_webhook_events():
    cursor = connection.cursor()

    while True:
        cursor.execute("SELECT payload, user_id, stack_id FROM github_webhookevents")
        rows = cursor.fetchall()

        if not rows:
            return "No more events to process", 200

        for row in rows:
            try:
                repo_url = row[0].get("repository").get("url")
                repo_name = row[0].get("repository").get("full_name")
                access_token = get_github_access_token(row[1])
                stack_id = row[2]

                repo_path = clone_repo(repo_url, repo_name, access_token)
                clone_user_repo(repo_path, stack_id)

            except Exception as e:
                print(f"Error processing event: {e}")

            finally:
                # Cleanup the cloned repo
                print("Cleaning up cloned repository")
                cursor.execute(
                    "DELETE FROM github_webhookevents WHERE user_id = %s", (row[1],)
                )
                connection.commit()


if __name__ == "__main__":
    database.connect_to_db()
    app.run(
        debug=True,
        host=os.environ.get("FLASK_RUN_HOST", "0.0.0.0"),
        port=os.environ.get("FLASK_RUN_PORT", "7654"),
    )
