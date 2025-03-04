from flask import Blueprint, jsonify, request, jsonify, send_file
from mongoDBUtils import deploy_mongodb
from GCPUtils import deploy_gcp
import os
import subprocess
import json
import time

api = Blueprint('api', __name__)

IMAGE_BASE_URL = "us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/"

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

    # Check if the file exists
    if not os.path.exists(f"./source_codes/{source_code}.tar"):
        return jsonify({"error": f"{source_code} does not exist"}), 404
    
    return send_file(f"./source_codes/{source_code}.tar", as_attachment=True)


