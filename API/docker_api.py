import os
import subprocess
from flask import Flask, request, jsonify, send_file
import json
import requests

app = Flask(__name__)

@app.route("/push-artifact", methods=["POST"])
def push_artifact():
    data = request.form['data']    
    data = json.loads(data)

    dockerBuildFile = request.form['dockerBuildFile']   

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
            f.write(dockerBuildFile)

            
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

@app.route("/pull-artifact/<url>", methods=["GET"])
def pull_artifact(url):
    container_url = "us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/" + url
    # Pull the Docker image
    os.system(f"docker pull {container_url}")
    
    # Save the Docker image to a tar file
    os.system(f"docker save {container_url} > ./test.tar")

    # Return the pulled image as a file
    return send_file("./test.tar", as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
