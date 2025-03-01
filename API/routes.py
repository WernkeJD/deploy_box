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

@api.route('/api/deployMERNStack', methods=['POST'])
def deploy_mern_stack():
    mongodb_uri = deploy_mongodb()
    deploy_gcp(mongodb_uri)
    return jsonify({"data": "MERN stack deployed successfully!"})

@api.route("/api/push-artifact", methods=["POST"])
def push_artifact():
    data = request.form['data']
    data = json.loads(data)

    docker_build_file = request.form['dockerBuildFile']   

    image_name = data.get("imageName")
    project_id = "deploy-box"
    repo = data.get("repo")
    region = "us-central1"

    if not all([image_name, project_id, repo, region]):
        return jsonify({"error": "Missing required fields" + " ".join([image_name, project_id, repo, region])}), 400

    full_image_name = f"{region}-docker.pkg.dev/{project_id}/{repo}/{image_name}:latest"

    try:
        # Download the Dockerfile
        with open("Dockerfile", "w") as f:
            f.write(docker_build_file)

            
        print(os.curdir)

        # Authenticate with GCP
        os.system(f"gcloud auth configure-docker {region}-docker.pkg.dev")

        # Build the Docker image
        os.system(f"docker build -t {full_image_name} .")

        # Push to Google Cloud Artifact Registry
        subprocess.run(["docker", "push", full_image_name], check=True)

        return jsonify({"message": "Artifact pushed successfully", "image": full_image_name})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

@api.route("/api/pull-artifact/<url>", methods=["GET"])
def pull_artifact(url):
    container_url = "us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/" + url
    # Pull the Docker image
    os.system(f"docker pull {container_url}")
    
    # Save the Docker image to a tar file
    os.system(f"docker save {container_url} > ./test.tar")

    # Return the pulled image as a file
    return send_file("./test.tar", as_attachment=True)

@api.route("/api/copy-artifacts", methods=["GET"])
def copy_artifacts():
    frontend_url = "kalebwbishop/mern-frontend"
    backend_url = "kalebwbishop/mern-backend"
    database_url = "kalebwbishop/mern-database:0.0.1"

    # Pull the Docker images
    os.system(f"docker pull {frontend_url}")
    os.system(f"docker pull {backend_url}")
    os.system(f"docker pull {database_url}")

    user_id = int(time.time())

    os.system("gcloud auth activate-service-account --key-file=key.json")
    os.system("gcloud auth configure-docker us-central1-docker.pkg.dev")


    # Retag the Docker images
    os.system(f"docker tag {frontend_url} {IMAGE_BASE_URL}{user_id}-mern-frontend:latest")
    os.system(f"docker tag {backend_url} {IMAGE_BASE_URL}{user_id}-mern-backend:latest")
    os.system(f"docker tag {database_url} {IMAGE_BASE_URL}{user_id}-mern-database:latest")

    # Push the Docker images
    os.system(f"docker push {IMAGE_BASE_URL}{user_id}-mern-frontend:latest")
    os.system(f"docker push {IMAGE_BASE_URL}{user_id}-mern-backend:latest")
    os.system(f"docker push {IMAGE_BASE_URL}{user_id}-mern-database:latest")

    return jsonify({"message": "Artifacts copied successfully"})