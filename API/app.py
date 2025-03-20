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
import logging
import shutil
import glob

logging.basicConfig(
    filename="deploy_box.log",  # Change or remove this to log to the console
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Set paths and credentials
current_working_dir = os.getcwd()
GCP_KEY_PATH = os.path.join(current_working_dir, "key.json")
PROJECT_ID = "deploy-box"
REGION = "us-central1"
name = f"projects/{PROJECT_ID}"
parent = f"{name}/locations/{REGION}"

app = Flask(__name__)
connection = database.get_connection()


@app.route("/", methods=["GET"])
def home():
    return "Deploy Box API is running.", 200


# Check if the GCP_KEY_PATH exists
if not os.path.exists(GCP_KEY_PATH):
    logging.error("Error: GCP key file not found.")
    raise FileNotFoundError("Error: GCP key file not found.")


# Helper function to load credentials
def get_credentials(scopes=None):
    logging.debug("Loading credentials from service account file.")
    with open(GCP_KEY_PATH, "r") as key_file:
        key_data = key_file.read()
        logging.debug(f"Credentials loaded successfully. {key_data}")

    return service_account.Credentials.from_service_account_file(
        GCP_KEY_PATH, scopes=scopes
    )


# Helper function to initialize services client
def get_services_client():
    logging.debug("Initializing Google Cloud services client.")
    return run_v2.ServicesClient(credentials=get_credentials())


def authenticate_docker():
    """Authenticate Docker using service account credentials."""
    logging.debug("Authenticating Docker with Google Cloud credentials.")
    credentials = get_credentials(
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    result = subprocess.run(
        ["gcloud", "auth", "activate-service-account", "--key-file", GCP_KEY_PATH],
        capture_output=True,
        text=True,
        check=True,
    )
    print("GCloud Authentication Output:", result.stdout)

    try:
        result = subprocess.run(
            [
                "gcloud",
                "auth",
                "configure-docker",
                "us-central1-docker.pkg.dev",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print("GCloud Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error running gcloud:", e.stderr)

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

    try:
        docker.from_env().login(**auth_config)
        logging.info("Docker authentication with Google Container Registry succeeded.")
    except Exception as e:
        logging.error(f"Docker authentication failed: {e}")


def prune_docker():
    subprocess.run(["docker", "system", "prune", "-af"], check=True)
    subprocess.run(["docker", "volume", "prune", "-f"], check=True)


def build_and_push_image(image_name, repo_path, tag: str = "latest"):
    """Builds and pushes a Docker image to Google Container Registry."""
    dockerfile_path = None
    for file in os.listdir(repo_path):
        if file.lower() == "dockerfile":
            dockerfile_path = os.path.join(repo_path, file)
            break

    if not os.path.exists(repo_path):
        logging.error(f"Error: Path {repo_path} does not exist.")
        raise FileNotFoundError(f"Error: Path {repo_path} does not exist.")
    if dockerfile_path is None:
        logging.error(f"Error: Dockerfile missing in {repo_path}.")
        raise FileNotFoundError(f"Error: Dockerfile missing in {repo_path}.")

    image_tag = f"us-central1-docker.pkg.dev/{PROJECT_ID}/deploy-box-repository/{image_name}:{tag}"

    logging.debug(f"Building Docker image: {image_tag}")
    authenticate_docker()

    result = subprocess.run(
        ["docker", "login", "us-central1-docker.pkg.dev"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)

    try:
        subprocess.run(["docker", "build", "-t", image_tag, repo_path], check=True)
        logging.info("Docker build completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error building Docker image: {e}")
        return

    try:
        subprocess.run(["docker", "push", image_tag], check=True)
        logging.info("Docker image pushed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error pushing Docker image: {e}")
        return

    return image_tag


# Function to refresh the service by updating the image
def refresh_service(service_name, image, tag="latest"):
    logging.debug(f"Refreshing service {service_name} with new image {image}:{tag}.")
    run_client = get_services_client()
    parent = f"projects/{PROJECT_ID}/locations/{REGION}"

    service_full_name = f"{parent}/services/{service_name}"
    service = run_client.get_service(name=service_full_name)

    service.template.containers[0].image = f"{image}:{tag}"
    try:
        operation = run_client.update_service(service=service)
        operation.result()  # Wait for deployment
        logging.info(f"Service {service_name} refreshed successfully.")
    except Exception as e:
        logging.error(f"Failed to refresh service {service_name}: {e}")


def clean_old_repos():
    """Removes old cloned repositories to free up space."""
    repo_dirs = glob.glob("deployed_repos/*")
    for repo_dir in repo_dirs:
        try:
            shutil.rmtree(repo_dir)
        except Exception as e:
            logging.error(f"Error deleting repo {repo_dir}: {e}")


def clone_repo(repo_url, repo_name, access_token):
    """Clones the given GitHub repository to the server."""
    repo_path = os.path.abspath(
        os.path.join(
            "deployed_repos",
            f"{repo_name}_{int(time.time())}",
        )
    ).replace("\\", "/")

    os.makedirs("deployed_repos", exist_ok=True)

    # Convert repo URL to use token authentication
    repo_url_with_auth = repo_url.replace(
        "https://github.com", f"https://{access_token}:x-oauth-basic@github.com"
    )

    logging.info(f"Starting to clone repository: {repo_url} into {repo_path}")

    try:
        subprocess.run(
            ["git", "clone", repo_url_with_auth, repo_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        logging.info(f"Successfully cloned repository into {repo_path}")
        return repo_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to clone repository: {repo_url} - Error: {e}")
        raise Exception(f"Failed to clone repository: {e}")


def clone_user_repo(repo_path, stack_id):
    logging.debug(f"Cloning user repository for stack {stack_id}.")

    tag = str(int(time.time()))

    try:
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
        logging.info(
            f"Successfully cloned and deployed user repository for stack {stack_id}."
        )
    except Exception as e:
        logging.error(f"Error during clone and deployment for stack {stack_id}: {e}")
        raise


ENCRYPTION_KEY = os.getenv("GITHUB_TOKEN_KEY")


def get_github_access_token(user_id: str):
    cursor = connection.cursor()

    logging.debug(f"Fetching GitHub access token for user ID: {user_id}.")
    cursor.execute(
        "SELECT encrypted_token FROM github_tokens WHERE user_id = %s", (user_id,)
    )
    rows = cursor.fetchone()
    cipher = Fernet(ENCRYPTION_KEY)
    decrypted_token = cipher.decrypt(rows[0].tobytes())
    decoded_token = decrypted_token.decode()
    logging.debug(
        f"Successfully fetched and decrypted GitHub access token for user {user_id}."
    )
    return decoded_token


@app.route("/github-webhook", methods=["GET"])
def get_github_webhook_events():
    logging.info("Processing GitHub webhook events.")

    # while True:
    cursor = connection.cursor()
    cursor.execute("SELECT id, payload, user_id, stack_id FROM github_webhookevents")
    rows = cursor.fetchall()

    if not rows:
        logging.info("No events found to process.")
        return "No more events to process", 200

    for row in rows:
        clean_old_repos()
        prune_docker()

        deployed_repos_path = os.path.join(current_working_dir, "deployed_repos")
        for root, dirs, files in os.walk(deployed_repos_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        logging.info("Cleaned up /app/deployed_repos folder.")
        try:
            repo_url = row[1].get("repository").get("url")
            repo_name = row[1].get("repository").get("full_name")
            access_token = get_github_access_token(row[2])
            stack_id = row[3]

            repo_path = clone_repo(repo_url, repo_name, access_token)
            clone_user_repo(repo_path, stack_id)

        except Exception as e:
            logging.error(f"Error processing event: {e}")

        finally:
            logging.debug("Cleaning up cloned repository.")
            # cursor.execute("DELETE FROM github_webhookevents WHERE id = %s", (row[0],))
            # connection.commit()


if __name__ == "__main__":
    # authenticate_docker()
    logging.info("Starting the Deploy Box application.")
    print(get_github_access_token("8"))
    # database.connect_to_db()
    # app.run(
    #     debug=True,
    #     host=os.environ.get("FLASK_RUN_HOST", "0.0.0.0"),
    #     port=os.environ.get("FLASK_RUN_PORT", "7654"),
    # )
