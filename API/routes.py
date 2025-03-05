from flask import Blueprint, jsonify, request, jsonify, send_file
from mongoDBUtils import deploy_mongodb
from GCPUtils import deploy_gcp
import os
import subprocess
import json
import time
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
    stack_type = request.form['stack-type']

    if stack_type not in ["MERN", "MEAN"]:
        return jsonify({"error": "Invalid stack type"}), 400
    
    source_code = request.files['source-code']

    if not source_code:
        return jsonify({"error": "No source code provided"}), 400
    
    if not os.path.exists("./temp"):
        os.makedirs("./temp")
    
    curr_time = int(time.time())
    temp_dir = f"./temp/{curr_time}"

    # Unpack the source code
    os.mkdir(temp_dir)
    source_code.save(f"{temp_dir}/sc.tar")
    os.system(f"tar -xf {temp_dir}/sc.tar -C {temp_dir}")


    # Build the Docker images
    os.system(f"docker build -t {IMAGE_BASE_URL}{stack_type.lower()}-frontend {temp_dir}/frontend")
    os.system(f"docker build -t {IMAGE_BASE_URL}{stack_type.lower()}-backend {temp_dir}/backend")

    # Push the Docker images
    subprocess.run(["docker", "push", f"{IMAGE_BASE_URL}{stack_type.lower()}-frontend"], check=True)
    subprocess.run(["docker", "push", f"{IMAGE_BASE_URL}{stack_type.lower()}-backend"], check=True)

    if stack_type == "MERN":
        deploy_mern_stack(f"{IMAGE_BASE_URL}{stack_type.lower()}-frontend", f"{IMAGE_BASE_URL}{stack_type.lower()}-backend")
    else:
        print("MEAN stack deployment not implemented yet")
    
    # Clean up
    os.system(f"rm -rf {temp_dir}")

    return jsonify({"message": "Artifact pushed successfully"})

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


