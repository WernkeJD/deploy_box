from flask import Blueprint, jsonify, request, jsonify, send_file
from mongoDBUtils import deploy_mongodb
from GCPUtils import deploy_service, refresh_service, get_blob
import subprocess
import tarfile
import io
import os
import time

api = Blueprint("api", __name__)

IMAGE_BASE_URL = "us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/"
BUCKET_NAME = "deploy_box_bucket"


@api.route("/")
def home():
    return jsonify({"message": "Welcome to the API!"})


def deploy_mern_stack(frontend_image: str, backend_image: str, deployment_id: str):
    mongodb_uri = deploy_mongodb(deployment_id)
    backend_url = deploy_service(
        f"backend-{deployment_id}", backend_image, {"MONGO_URI": mongodb_uri}
    )
    frontend_url = deploy_service(
        f"frontend-{deployment_id}",
        frontend_image,
        {"REACT_APP_BACKEND_URL": backend_url},
    )

    return frontend_url, backend_url, mongodb_uri


def refresh_mern_stack(frontend_image: str, backend_image: str, deployment_id: str):
    refresh_service(f"backend-{deployment_id}", backend_image)
    refresh_service(f"frontend-{deployment_id}", frontend_image)


@api.route("/api/code", methods=["POST"])
def push_code():
    content_length = request.content_length
    print(f"Attempted content length: {content_length} bytes")

    # Can be MERN or MEAN
    stack_type = request.form.get("stack-type")
    print(f"Stack type: {stack_type}")
    print(f"Deployment ID: {request.form.get('deployment-id')}")
    deployment_id = request.form.get("deployment-id")

    if not stack_type:
        return jsonify({"error": "Stack type not provided"}), 400

    if not deployment_id:
        return jsonify({"error": "Deployment ID not provided"}), 400

    if stack_type not in ["MERN", "MEAN"]:
        return jsonify({"error": "Invalid stack type"}), 400

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Save the file to the local filesystem
    file.save("uploaded_file.tar")

    # Extract the tar file to a specific directory
    with tarfile.open("uploaded_file.tar", "r") as tar:
        tar.extractall("./extracted_files")

    # Define the files to be included in the Docker image
    frontend_dir = "./extracted_files/frontend"
    backend_dir = "./extracted_files/backend"

    # Build and push the Docker images
    curr_time = int(time.time())
    frontend_image_tag = f"{IMAGE_BASE_URL}frontend-{deployment_id}:{curr_time}"
    backend_image_tag = f"{IMAGE_BASE_URL}backend-{deployment_id}:{curr_time}"

    build_and_push_docker_image(frontend_dir, frontend_image_tag)
    build_and_push_docker_image(backend_dir, backend_image_tag)

    frontend_url = None
    backend_url = None
    database_url = None

    if stack_type == "MERN":
        frontend_url, backend_url, database_url = deploy_mern_stack(
            frontend_image_tag, backend_image_tag, deployment_id
        )
    else:
        print("MEAN stack deployment not implemented yet")

    print(f"Frontend URL: {frontend_url}")
    print(f"Backend URL: {backend_url}")
    print(f"Database URL: {database_url}")

    return jsonify(
        {
            "frontend_id": frontend_url,
            "frontend_image": frontend_image_tag,
            "backend_id": backend_url,
            "backend_image": backend_image_tag,
            "database_uri": database_url,
        }
    )


@api.route("/api/code", methods=["PATCH"])
def patch_code():
    content_length = request.content_length
    print(f"Attempted content length: {content_length} bytes")

    # Can be MERN or MEAN
    stack_type = request.form.get("stack-type")
    print(f"Stack type: {stack_type}")
    print(f"Deployment ID: {request.form.get('deployment-id')}")
    deployment_id = request.form.get("deployment-id")

    if not stack_type:
        return jsonify({"error": "Stack type not provided"}), 400

    if not deployment_id:
        return jsonify({"error": "Deployment ID not provided"}), 400

    if stack_type not in ["MERN", "MEAN"]:
        return jsonify({"error": "Invalid stack type"}), 400

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Save the file to the local filesystem
    file.save("uploaded_file.tar")

    # Extract the tar file to a specific directory
    with tarfile.open("uploaded_file.tar", "r") as tar:
        tar.extractall("./extracted_files")

    # Define the files to be included in the Docker image
    frontend_dir = "./extracted_files/frontend"
    backend_dir = "./extracted_files/backend"

    # Build and push the Docker images
    curr_time = int(time.time())
    frontend_image_tag = f"{IMAGE_BASE_URL}frontend-{deployment_id}:{curr_time}"
    backend_image_tag = f"{IMAGE_BASE_URL}backend-{deployment_id}:{curr_time}"

    build_and_push_docker_image(frontend_dir, frontend_image_tag)
    build_and_push_docker_image(backend_dir, backend_image_tag)

    if stack_type == "MERN":
        refresh_mern_stack(frontend_image_tag, backend_image_tag, deployment_id)
    else:
        print("MEAN stack deployment not implemented yet")

    return jsonify(
        {
            "message": "Successfully updated deployment",
        }
    )


def build_and_push_docker_image(directory, image_name):
    # Convert relative directory to absolute path
    directory = os.path.abspath(directory)

    print(f"Building Docker image from {directory} with name {image_name}")

    # Build the Docker image from the given directory
    subprocess.run(["docker", "build", "-t", image_name, directory], check=True)

    # Push the Docker image
    subprocess.run(["docker", "push", image_name], check=True)


@api.route("/api/code/<source_code>", methods=["GET"])
def pull_code(source_code: str):
    source_code = source_code.upper()

    # Define the bucket and file path
    file_name = f"{source_code}.tar"

    # Access the GCS bucket
    blob = get_blob(file_name)

    # Check if the blob exists in the bucket
    if not blob.exists():
        return jsonify({"error": f"{source_code} does not exist"}), 404

    # Stream the file to the user as an attachment
    file_stream = io.BytesIO()
    blob.download_to_file(file_stream)
    file_stream.seek(0)

    # Send the file to the user
    return send_file(file_stream, as_attachment=True, download_name=file_name)
