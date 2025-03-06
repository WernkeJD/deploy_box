from flask import Blueprint, jsonify, request, jsonify, send_file
from mongoDBUtils import deploy_mongodb
from GCPUtils import deploy_gcp
import subprocess
import tarfile
from google.cloud import storage
import io

api = Blueprint('api', __name__)

IMAGE_BASE_URL = "us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/"
BUCKET_NAME = "deploy_box_bucket"

storage_client = storage.Client()

@api.route('/')
def home():
    return jsonify({'message': 'Welcome to the API!'})

def deploy_mern_stack(frontend_image: str, backend_image: str):
    mongodb_uri = deploy_mongodb()
    deploy_gcp(mongodb_uri, frontend_image, backend_image)
    return jsonify({"data": "MERN stack deployed successfully!"})

@api.route("/api/push-code", methods=["POST"])
def push_code():
    # Can be MERN or MEAN
    stack_type = request.form.get("stack-type")

    if stack_type not in ["MERN", "MEAN"]:
        return jsonify({"error": "Invalid stack type"}), 400

    source_code = request.files.get("source-code")

    if not source_code:
        return jsonify({"error": "No source code provided"}), 400

    # Read the uploaded tar file into memory
    tar_bytes = io.BytesIO(source_code.read())

    with tarfile.open(fileobj=tar_bytes, mode="r:*") as tar:
        members = tar.getmembers()
        
        # Ensure the tar file contains expected directories
        if not any(m.name.startswith("frontend/") for m in members) or not any(m.name.startswith("backend/") for m in members):
            return jsonify({"error": "Invalid source structure. Expecting 'frontend' and 'backend' directories."}), 400

        # Extract frontend files into memory
        frontend_files = {m.name: tar.extractfile(m).read() for m in members if m.name.startswith("frontend/") and m.isfile()}
        backend_files = {m.name: tar.extractfile(m).read() for m in members if m.name.startswith("backend/") and m.isfile()}

    # Build and push the Docker images (without writing files to disk)
    build_and_push_docker_image(frontend_files, f"{IMAGE_BASE_URL}{stack_type.lower()}-frontend")
    build_and_push_docker_image(backend_files, f"{IMAGE_BASE_URL}{stack_type.lower()}-backend")

    if stack_type == "MERN":
        deploy_mern_stack(f"{IMAGE_BASE_URL}{stack_type.lower()}-frontend", f"{IMAGE_BASE_URL}{stack_type.lower()}-backend")
    else:
        print("MEAN stack deployment not implemented yet")

    return jsonify({"message": "Artifact pushed successfully"})


def build_and_push_docker_image(files, image_name):
    """Builds a Docker image using an in-memory context."""
    with io.BytesIO() as dockerfile_context:
        with tarfile.open(fileobj=dockerfile_context, mode="w") as tar:
            for filename, filedata in files.items():
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(filedata)
                tar.addfile(tarinfo, io.BytesIO(filedata))
        
        dockerfile_context.seek(0)
        
        # Build the Docker image from the in-memory context
        subprocess.run(["docker", "build", "-t", image_name, "-"], input=dockerfile_context.read(), check=True)

    # Push the Docker image
    subprocess.run(["docker", "push", image_name], check=True)


@api.route("/api/pull-code/<source_code>", methods=["GET"])
def pull_code(source_code: str):
    source_code = source_code.upper()

    # Define the bucket and file path
    file_name = f"{source_code}.tar"

    # Access the GCS bucket
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)

    # Check if the blob exists in the bucket
    if not blob.exists():
        return jsonify({"error": f"{source_code} does not exist"}), 404

    # Stream the file to the user as an attachment
    file_stream = io.BytesIO()
    blob.download_to_file(file_stream)
    file_stream.seek(0)

    # Send the file to the user
    return send_file(file_stream, as_attachment=True, download_name=file_name)


