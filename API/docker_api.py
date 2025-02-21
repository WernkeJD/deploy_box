import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/push-artifact", methods=["POST"])
def push_artifact():
    data = request.get_json()

    image_name = data.get("imageName")
    project_id = "deploy-box"
    repo = data.get("repo")
    region = "us-central1"
    container_path = data.get("containerPath")
    dockerfile_path = data.get("dockerfilePath")

    if not all([image_name, project_id, repo, region]):
        return jsonify({"error": "Missing required fields" + " ".join([image_name, project_id, repo, region])}), 400

    os.chdir("../docker/MERN/frontend")
    print(os.listdir())

    full_image_name = f"{region}-docker.pkg.dev/{project_id}/{repo}/{image_name}:latest"

    try:

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
